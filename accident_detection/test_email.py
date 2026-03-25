"""
Test Email Alert System
Run this to test if email alerts are working.
"""
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accident_detection.settings')
import django
django.setup()

from video_processor.alert_system import AlertSystem

def test_email():
    print("Testing email alert system...")

    alert_system = AlertSystem()

    # Create a test alert
    alert = alert_system.generate_alert(
        confidence=0.85,
        location='Test Location',
        video_id='test_video',
        frame_number=100,
        vehicle_count=3,
        overlap_score=0.6,
    )

    print("Test alert generated:")
    print(f"  Level: {alert['alert_level']}")
    print(f"  Confidence: {alert['confidence_percentage']}%")
    print(f"  Location: {alert['location']}")

    print("Check your email and console for the alert message.")

if __name__ == "__main__":
    test_email()