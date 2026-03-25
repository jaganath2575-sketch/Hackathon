"""
Optimized Video-Level Accident Detection System
Processes videos efficiently with frame skipping and single decision per video
"""

import cv2
import os
import logging
from datetime import datetime
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedVideoProcessor:
    """
    Efficient video processor that works at VIDEO LEVEL, not frame level
    """

    def __init__(self, video_path, frame_skip=5, accident_threshold=3):
        """
        Initialize video processor

        Args:
            video_path: Path to video file
            frame_skip: Process every Nth frame (default: 5)
            accident_threshold: Minimum accident detections to confirm (default: 3)
        """
        self.video_path = video_path
        self.frame_skip = frame_skip
        self.accident_threshold = accident_threshold
        self.cap = None
        self.video_id = None

    def generate_video_id(self):
        """Generate unique video ID"""
        # Simple ID generation - in real app, use database counter
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"video_{timestamp}"

    def open_video(self):
        """Open video file"""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise Exception(f"Could not open video: {self.video_path}")
        return True

    def get_video_info(self):
        """Get basic video information"""
        if not self.cap:
            return None

        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return {
            'total_frames': total_frames,
            'fps': fps,
            'width': width,
            'height': height,
            'duration': total_frames / fps if fps > 0 else 0
        }

    def detect_vehicles_simple(self, frame):
        """
        Simple vehicle detection (replace with YOLO in real implementation)
        Returns number of detected vehicles
        """
        # Convert to grayscale for simple processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Simple motion detection (placeholder for YOLO)
        # In real implementation, use: detections = yolo_detector.get_vehicle_detections(frame)
        vehicle_count = np.random.randint(0, 5)  # Random for demo

        return vehicle_count

    def analyze_frame_for_accident(self, vehicle_count):
        """
        Simple accident analysis (replace with real accident detector)
        Returns True if accident detected in this frame
        """
        # Simple logic: accident if 3+ vehicles detected
        # In real implementation, use proper accident detection algorithm
        return vehicle_count >= 3

    def process_video_efficiently(self):
        """
        MAIN METHOD: Process entire video efficiently at VIDEO LEVEL

        Returns:
            dict: Final video-level results
        """
        logger.info(f"Starting VIDEO-LEVEL processing for: {os.path.basename(self.video_path)}")

        # Generate unique video ID
        self.video_id = self.generate_video_id()
        logger.info(f"Assigned Video ID: {self.video_id}")

        # Open video
        self.open_video()
        video_info = self.get_video_info()
        logger.info(f"Video info: {video_info['total_frames']} frames, {video_info['fps']:.1f} FPS")

        # VIDEO-LEVEL PROCESSING VARIABLES
        frame_count = 0
        processed_frames = 0
        accident_detections = []  # Store all accident detections
        confidence_scores = []    # Store confidence scores
        vehicle_counts = []       # Store vehicle counts per accident frame
        alert_sent = False        # Single alert flag

        logger.info(f"Frame skip rate: {self.frame_skip} (processing every {self.frame_skip}th frame)")

        # EFFICIENT VIDEO PROCESSING LOOP
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame_count += 1

            # FRAME SKIPPING OPTIMIZATION
            if frame_count % self.frame_skip != 0:
                continue

            processed_frames += 1

            # PERFORMANCE OPTIMIZATION: Resize frame
            frame_resized = cv2.resize(frame, (640, 480))

            # DETECT VEHICLES (replace with YOLO)
            vehicle_count = self.detect_vehicles_simple(frame_resized)

            # Skip frames with no vehicles (optimization)
            if vehicle_count == 0:
                continue

            logger.info(f"Frame {frame_count}: Detected {vehicle_count} vehicles")

            # ANALYZE FOR ACCIDENT (FRAME-LEVEL analysis)
            is_accident = self.analyze_frame_for_accident(vehicle_count)

            if is_accident:
                # Store accident detection data
                accident_data = {
                    'frame_number': frame_count,
                    'vehicle_count': vehicle_count,
                    'confidence': 0.85,  # Placeholder confidence
                    'timestamp': frame_count / video_info['fps']
                }

                accident_detections.append(accident_data)
                confidence_scores.append(accident_data['confidence'])
                vehicle_counts.append(vehicle_count)

                logger.info(f"🚨 Accident detected at frame {frame_count} (vehicles: {vehicle_count})")

        # VIDEO-LEVEL DECISION MAKING
        logger.info(f"Processing complete. Analyzed {processed_frames} frames out of {video_info['total_frames']} total frames")
        logger.info(f"Accident detections: {len(accident_detections)}")

        # FINAL VIDEO-LEVEL DECISION
        accident_detected = len(accident_detections) >= self.accident_threshold

        if accident_detected:
            # Calculate aggregated metrics
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            avg_vehicles = sum(vehicle_counts) / len(vehicle_counts)
            best_frame = max(accident_detections, key=lambda x: x['confidence'])

            final_result = {
                'video_id': self.video_id,
                'accident_detected': True,
                'confidence_score': avg_confidence,
                'total_frames_processed': processed_frames,
                'accident_frames': len(accident_detections),
                'avg_vehicles_involved': avg_vehicles,
                'best_detection_frame': best_frame['frame_number'],
                'alert_sent': True,
                'description': f"Video-level accident confirmed: {len(accident_detections)} detections across {processed_frames} analyzed frames"
            }

            logger.info(f"🎯 FINAL DECISION: ACCIDENT CONFIRMED")
            logger.info(f"   - Confidence: {avg_confidence:.2f}")
            logger.info(f"   - Accident frames: {len(accident_detections)}")
            logger.info(f"   - Avg vehicles: {avg_vehicles:.1f}")

        else:
            final_result = {
                'video_id': self.video_id,
                'accident_detected': False,
                'confidence_score': 0.0,
                'total_frames_processed': processed_frames,
                'accident_frames': 0,
                'avg_vehicles_involved': 0,
                'best_detection_frame': None,
                'alert_sent': False,
                'description': f"No accident detected in {processed_frames} analyzed frames"
            }

            logger.info(f"✅ FINAL DECISION: NO ACCIDENT DETECTED")

        # Clean up
        self.cap.release()

        return final_result

def main():
    """Example usage"""
    # Example video path (change to your video)
    video_path = "sample_video.mp4"

    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        logger.info("Please provide a valid video file path")
        return

    # Create optimized processor
    processor = OptimizedVideoProcessor(
        video_path=video_path,
        frame_skip=5,           # Process every 5th frame
        accident_threshold=3    # Need 3+ accident detections to confirm
    )

    try:
        # Process video efficiently
        result = processor.process_video_efficiently()

        # Display results
        print("\n" + "="*50)
        print("VIDEO-LEVEL ACCIDENT DETECTION RESULTS")
        print("="*50)
        print(f"Video ID: {result['video_id']}")
        print(f"Accident Detected: {'YES' if result['accident_detected'] else 'NO'}")
        print(f"Confidence Score: {result['confidence_score']:.2f}")
        print(f"Frames Processed: {result['total_frames_processed']}")
        print(f"Accident Frames: {result['accident_frames']}")
        print(f"Average Vehicles: {result['avg_vehicles_involved']:.1f}")
        print(f"Alert Sent: {'YES' if result['alert_sent'] else 'NO'}")
        print(f"Description: {result['description']}")
        print("="*50)

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")

if __name__ == "__main__":
    main()