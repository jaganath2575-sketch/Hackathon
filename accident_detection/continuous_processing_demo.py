"""
Test Script for Continuous Video Processing
Demonstrates analyzing complete video without frame skipping
"""

import cv2
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_continuous_test_video(output_path="continuous_test.mp4", duration_seconds=5, fps=30):
    """
    Create a test video for continuous processing demonstration
    """
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_num in range(duration_seconds * fps):
        # Create a frame with moving vehicles
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Add moving vehicles (simulate traffic)
        num_vehicles = np.random.randint(1, 5)  # Always at least 1 vehicle

        for i in range(num_vehicles):
            # Vehicles move from left to right
            x = (frame_num * 3 + i * 150) % (width + 100) - 50
            y = height // 2 + np.random.randint(-30, 30)

            # Create accident scenario: vehicles cluster together occasionally
            if frame_num > 60 and frame_num < 90:  # Frames 60-90: accident period
                x = width // 2 + np.random.randint(-20, 20)  # Cluster vehicles
                y = height // 2 + np.random.randint(-10, 10)

            cv2.rectangle(frame, (x, y), (x + 40, y + 25), (0, 255, 0), -1)

        # Add frame info
        cv2.putText(frame, f"Frame: {frame_num}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        if frame_num > 60 and frame_num < 90:
            cv2.putText(frame, "ACCIDENT ZONE", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        out.write(frame)

    out.release()
    logger.info(f"Continuous test video created: {output_path}")

def continuous_video_analysis_demo(video_path):
    """
    Demonstrate continuous video analysis without frame skipping
    """
    logger.info("="*70)
    logger.info("CONTINUOUS VIDEO ANALYSIS DEMO (NO FRAME SKIPPING)")
    logger.info("="*70)

    # Generate unique video ID
    video_id = f"continuous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"🎬 Processing Video ID: {video_id}")
    logger.info(f"📁 Video Path: {video_path}")

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return None

    # Get video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"📊 Video Info: {total_frames} frames, {fps:.1f} FPS, Duration: {total_frames/fps:.1f}s")

    # CONTINUOUS ANALYSIS VARIABLES
    frame_count = 0
    accident_detections = []
    confidence_scores = []
    vehicle_counts = []

    logger.info("🚀 Starting CONTINUOUS video analysis (processing EVERY frame)...")

    # Store previous frame detections for motion analysis
    previous_detections = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # CONTINUOUS PROCESSING: Analyze EVERY frame (no skipping)
        logger.debug(f"Processing frame {frame_count}/{total_frames}")

        # Resize frame
        frame_resized = cv2.resize(frame, (640, 480))

        # SIMULATE VEHICLE DETECTION (replace with YOLO)
        # Count green rectangles (vehicles) in the frame
        hsv = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2HSV)
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        vehicle_count = len(contours)
        detections = []

        # Create detection objects
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            detections.append({
                'bbox': (x, y, x+w, y+h),
                'confidence': 0.9,
                'class': 'vehicle'
            })

        # CONTINUOUS ACCIDENT ANALYSIS
        if vehicle_count >= 2:  # Potential accident if 2+ vehicles
            # Check for clustering (accident indicator)
            centers = []
            for detection in detections:
                x1, y1, x2, y2 = detection['bbox']
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                centers.append((center_x, center_y))

            # Calculate distances between vehicle centers
            cluster_score = 0
            if len(centers) >= 2:
                distances = []
                for i in range(len(centers)):
                    for j in range(i+1, len(centers)):
                        dist = np.sqrt((centers[i][0] - centers[j][0])**2 +
                                     (centers[i][1] - centers[j][1])**2)
                        distances.append(dist)

                avg_distance = np.mean(distances) if distances else 100
                # Lower distance = higher clustering = potential accident
                cluster_score = max(0, 1 - (avg_distance / 100))

            # Motion analysis (compare with previous frame)
            motion_score = 0
            if previous_detections and len(previous_detections) == len(detections):
                # Simple motion analysis: check if vehicles have moved significantly
                total_movement = 0
                for i, curr in enumerate(centers):
                    if i < len(previous_detections):
                        prev_center = ((previous_detections[i]['bbox'][0] + previous_detections[i]['bbox'][2]) / 2,
                                     (previous_detections[i]['bbox'][1] + previous_detections[i]['bbox'][3]) / 2)
                        movement = np.sqrt((curr[0] - prev_center[0])**2 + (curr[1] - prev_center[1])**2)
                        total_movement += movement

                avg_movement = total_movement / len(detections)
                motion_score = min(1.0, avg_movement / 50)  # Normalize movement

            # Calculate accident confidence
            confidence = (cluster_score * 0.6) + (motion_score * 0.4)
            confidence = min(1.0, confidence)

            # Accident detection threshold
            accident_detected = confidence > 0.3 or cluster_score > 0.5

            if accident_detected:
                accident_detections.append({
                    'frame_number': frame_count,
                    'confidence': confidence,
                    'vehicle_count': vehicle_count,
                    'cluster_score': cluster_score,
                    'motion_score': motion_score,
                    'timestamp': frame_count / fps
                })
                confidence_scores.append(confidence)
                vehicle_counts.append(vehicle_count)

                logger.info(f"🚨 ACCIDENT DETECTED at frame {frame_count}!")
                logger.info(f"   📊 Vehicles: {vehicle_count}, Confidence: {confidence:.2f}")
                logger.info(f"   🎯 Clustering: {cluster_score:.2f}, Motion: {motion_score:.2f}")

        # Update previous detections for next frame
        previous_detections = detections.copy()

    cap.release()

    # CONTINUOUS VIDEO DECISION MAKING
    logger.info("\n📈 CONTINUOUS ANALYSIS COMPLETE")
    logger.info(f"   Total frames processed: {frame_count}")
    logger.info(f"   Accident detections: {len(accident_detections)}")

    # FINAL DECISION BASED ON CONTINUOUS ANALYSIS
    accident_detected = len(accident_detections) > 0

    if accident_detected:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        avg_vehicles = sum(vehicle_counts) / len(vehicle_counts)
        best_detection = max(accident_detections, key=lambda x: x['confidence'])

        result = {
            'video_id': video_id,
            'accident_detected': True,
            'final_confidence': avg_confidence,
            'accident_frames': len(accident_detections),
            'avg_vehicles': avg_vehicles,
            'best_frame': best_detection['frame_number'],
            'alert_sent': True,
            'description': f"Continuous analysis: Accident in {len(accident_detections)} frames",
            'processing_type': 'continuous'
        }

        logger.info("\n🎯 FINAL RESULT: ACCIDENT DETECTED!")
        logger.info(f"   🎬 Video ID: {video_id}")
        logger.info(f"   📊 Confidence: {avg_confidence:.2f}")
        logger.info(f"   🚗 Avg Vehicles: {avg_vehicles:.1f}")
        logger.info(f"   🎯 Best Frame: {best_detection['frame_number']}")

    else:
        result = {
            'video_id': video_id,
            'accident_detected': False,
            'final_confidence': 0.0,
            'accident_frames': 0,
            'avg_vehicles': 0,
            'best_frame': None,
            'alert_sent': False,
            'description': "No accident detected in continuous analysis",
            'processing_type': 'continuous'
        }

        logger.info("\n✅ FINAL RESULT: NO ACCIDENT DETECTED")
        logger.info(f"   🎬 Video ID: {video_id}")

    logger.info("="*70)
    return result

def main():
    """Main demo function"""
    print("🚗 Continuous Video Analysis Demo (No Frame Skipping)")
    print("=" * 55)

    video_path = "continuous_test.mp4"

    # Create test video if it doesn't exist
    import os
    if not os.path.exists(video_path):
        print("Creating continuous test video...")
        create_continuous_test_video(video_path, duration_seconds=5)

    # Run continuous analysis
    result = continuous_video_analysis_demo(video_path)

    if result:
        print("\n📋 SUMMARY:")
        print(f"   Video ID: {result['video_id']}")
        print(f"   Processing: {result['processing_type']}")
        print(f"   Accident: {'YES' if result['accident_detected'] else 'NO'}")
        print(f"   Confidence: {result['final_confidence']:.2f}")
        print(f"   Accident: {'YES' if result['accident_detected'] else 'NO'}")
        print(f"   Confidence: {result['final_confidence']:.2f}")
        print(f"   Alert Sent: {'YES' if result['alert_sent'] else 'NO'}")

if __name__ == "__main__":
    main()