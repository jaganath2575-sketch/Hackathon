"""
Alert system for accident notifications.
"""
import logging
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


class AlertSystem:
    """
    Generates and manages accident alerts.
    
    Features:
    - Alert generation on accident confirmation
    - Console logging with formatted output
    - Alert storage for dashboard display
    """
    
    def __init__(self):
        """Initialize alert system."""
        self.alerts = []
        logger.info("AlertSystem initialized")
    
    def generate_alert(
        self,
        confidence,
        location='Unknown Location',
        video_id='video_001',
        frame_number=0,
        vehicle_count=0,
        overlap_score=0,
        **kwargs
    ):
        """
        Generate an accident alert.
        
        Args:
            confidence (float): Detection confidence (0-1)
            location (str): Location/camera ID
            video_id (str): Video file identifier
            frame_number (int): Frame number where accident detected
            vehicle_count (int): Number of vehicles involved
            overlap_score (float): Vehicle overlap score
            **kwargs: Additional alert data
        
        Returns:
            dict: Alert object
        """
        alert = {
            'timestamp': datetime.now(),
            'confidence': confidence,
            'confidence_percentage': confidence * 100,
            'location': location,
            'video_id': video_id,
            'frame_number': frame_number,
            'vehicle_count': vehicle_count,
            'overlap_score': overlap_score,
            'alert_level': self._determine_alert_level(confidence),
            **kwargs,
        }
        
        self.alerts.append(alert)
        self._print_alert(alert)
        self._send_email_alert(alert)
        
        return alert
    
    def _determine_alert_level(self, confidence):
        """
        Determine alert severity level based on confidence.
        
        Args:
            confidence (float): Detection confidence (0-1)
        
        Returns:
            str: Alert level (LOW, MEDIUM, HIGH, CRITICAL)
        """
        if confidence >= 0.9:
            return 'CRITICAL'
        elif confidence >= 0.7:
            return 'HIGH'
        elif confidence >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _print_alert(self, alert):
        """
        Print formatted alert to console.
        
        Args:
            alert (dict): Alert object
        """
        alert_level = alert['alert_level']
        timestamp = alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        confidence = alert['confidence_percentage']
        location = alert['location']
        vehicles = alert['vehicle_count']
        frame = alert['frame_number']
        
        # Create formatted alert message
        print("\n" + "=" * 80)
        print(f"🚨 ACCIDENT DETECTED - ALERT LEVEL: {alert_level}")
        print("=" * 80)
        print(f"Timestamp:        {timestamp}")
        print(f"Location:         {location}")
        print(f"Video ID:         {alert['video_id']}")
        print(f"Frame Number:     {frame}")
        print(f"Confidence:       {confidence:.2f}%")
        print(f"Vehicles:         {vehicles}")
        print(f"Overlap Score:    {alert['overlap_score']:.3f}")
        print("=" * 80 + "\n")
        
        # Also log to file
        logger.critical(
            f"ACCIDENT ALERT - Level: {alert_level}, "
            f"Location: {location}, "
            f"Confidence: {confidence:.2f}%, "
            f"Vehicles: {vehicles}"
        )
    
    def _send_email_alert(self, alert):
        """
        Send email alert for accident detection.
        
        Args:
            alert (dict): Alert object
        """
        try:
            subject = f"🚨 ACCIDENT DETECTED - {alert['alert_level']} Alert"
            timestamp = alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            message = f"""
Accident Detected!

Location: {alert['location']}
Time of Detection: {timestamp}
Confidence: {alert['confidence_percentage']:.2f}%
Vehicles Involved: {alert['vehicle_count']}
Alert Level: {alert['alert_level']}

Please check the system dashboard for more details.
"""
            recipients = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
            print(f"DEBUG: Attempting to send email to {recipients}")
            if recipients:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=recipients,
                    fail_silently=False,
                )
                logger.info(f"Email alert sent to {recipients}")
                print(f"DEBUG: Email sent successfully to {recipients}")
            else:
                logger.warning("No email recipients configured for alerts")
                print("DEBUG: No email recipients configured")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            print(f"DEBUG: Email sending failed: {e}")
    
    def get_recent_alerts(self, limit=10):
        """
        Get recent alerts.
        
        Args:
            limit (int): Maximum number of alerts to return
        
        Returns:
            list: Recent alerts sorted by timestamp (newest first)
        """
        return sorted(
            self.alerts[-limit:],
            key=lambda x: x['timestamp'],
            reverse=True
        )
    
    def get_alerts_by_location(self, location):
        """
        Get alerts from specific location.
        
        Args:
            location (str): Location name
        
        Returns:
            list: Alerts from that location
        """
        return [a for a in self.alerts if a['location'] == location]
    
    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts.clear()
        logger.info("All alerts cleared")
    
    def get_alert_statistics(self):
        """
        Get alert statistics.
        
        Returns:
            dict: Statistics about alerts
        """
        if not self.alerts:
            return {
                'total_alerts': 0,
                'critical_alerts': 0,
                'high_alerts': 0,
                'avg_confidence': 0,
            }
        
        return {
            'total_alerts': len(self.alerts),
            'critical_alerts': sum(1 for a in self.alerts if a['alert_level'] == 'CRITICAL'),
            'high_alerts': sum(1 for a in self.alerts if a['alert_level'] == 'HIGH'),
            'medium_alerts': sum(1 for a in self.alerts if a['alert_level'] == 'MEDIUM'),
            'low_alerts': sum(1 for a in self.alerts if a['alert_level'] == 'LOW'),
            'avg_confidence': sum(a['confidence'] for a in self.alerts) / len(self.alerts),
            'unique_locations': len(set(a['location'] for a in self.alerts)),
        }
