"""
Live Accident Detection with Cooldown and Email Alert
"""
import os, sys, time, cv2
from datetime import datetime, timedelta

# Append project root for django apps
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accident_detection.settings')

import django
django.setup()

from video_processor.yolo_detector import YOLODetector
from video_processor.accident_detector import AccidentDetector
from video_processor.alert_system import AlertSystem

COOLDOWN_SECONDS = 12


def main():
    detector = YOLODetector()
    detector.load_model()

    accident_detector = AccidentDetector()
    alert_system = AlertSystem()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('ERROR: Cannot open camera')
        return

    alert_sent = False
    last_alert_time = datetime.min
    detection_active = False

    print('Live detection started. Press q to quit.')

    while True:
        ret, frame = cap.read()
        if not ret:
            print('ERROR: Failed to read frame')
            break

        # Get detections from YOLO
        detections = detector.get_vehicle_detections(frame)
        print(f'[DEBUG] frame detections count={len(detections)}')

        for i, det in enumerate(detections):
            print(f"  [DEBUG] det {i}: id={det['class_id']} name={det['class_name']} conf={det['confidence']:.3f}")
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{det['class_name']} {det['confidence']:.2f}", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        analysis = accident_detector.analyze_frame(detections, None)
        print(f"[DEBUG] analyze accident_detected={analysis['accident_detected']} confidence={analysis['confidence']:.3f}")

        if analysis['accident_detected']:
            detection_active = True
            accident_detector.add_frame_to_buffer(detections, analysis)
            confirmation = accident_detector.confirm_accident()
            print(f"[DEBUG] confirmation accident_confirmed={confirmation['accident_confirmed']} confidence={confirmation['confidence']:.3f}")

            if confirmation['accident_confirmed']:
                now = datetime.now()
                cooldown_done = (now - last_alert_time).total_seconds() >= COOLDOWN_SECONDS

                if not alert_sent or cooldown_done:
                    print('[DEBUG] CALLING EMAIL FUNCTION')
                    try:
                        alert_system.generate_alert(
                            confidence=confirmation['confidence'],
                            location='Live Camera',
                            video_id='live',
                            frame_number=0,
                            vehicle_count=len(detections),
                            overlap_score=confirmation.get('avg_overlap', 0),
                        )
                        print('[DEBUG] Email send attempt complete')
                    except Exception as ex:
                        print(f'[DEBUG] Email function raised exception: {ex}')

                    alert_sent = True
                    last_alert_time = now
                else:
                    print('[DEBUG] in cooldown, email call skipped')

                # show on-screen alert
                cv2.putText(frame, 'ACCIDENT DETECTED', (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 255), 4)
                cv2.putText(frame, f'Confidence: {confirmation["confidence"]:.2f}', (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            else:
                print('[DEBUG] not enough confirm. no alert sent')

        else:
            if detection_active:
                print('[DEBUG] accident ended, resetting alert state')
            detection_active = False
            alert_sent = False

        cv2.imshow('Live Accident Detection', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print('Live detection finished')


if __name__ == '__main__':
    main()
