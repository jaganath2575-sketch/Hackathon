"""
Test Script for Optimized Video Processing
Demonstrates efficient video-level accident detection
"""

import cv2
import numpy as np
import logging
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_video(output_path="sample_video.mp4", duration_seconds=10, fps=30):
    """
    Create a sample video for testing (optional)
    """
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame_num in range(duration_seconds * fps):
        # Create a simple frame with moving objects
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        # Add some moving rectangles (simulating vehicles)
        num_vehicles = np.random.randint(0, 4)
        for i in range(num_vehicles):
            x = (frame_num * 5 + i * 100) % (width + 100) - 50
            y = height // 2 + np.random.randint(-50, 50)
            cv2.rectangle(frame, (x, y), (x + 50, y + 30), (0, 255, 0), -1)

        # Add frame number
        cv2.putText(frame, f"Frame: {frame_num}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        out.write(frame)

    out.release()
    logger.info(f"Sample video created: {output_path}")

def optimized_video_processing_demo(video_path, frame_skip=5, accident_threshold=3):
    """
    Demonstrate optimized video processing with frame skipping
    """
    logger.info("="*60)
    logger.info("OPTIMIZED VIDEO-LEVEL ACCIDENT DETECTION DEMO")
    logger.info("="*60)

    # Generate unique video ID
    video_id = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"🎬 Processing Video ID: {video_id}")
    logger.info(f"📁 Video Path: {video_path}")
    logger.info(f"⏭️  Frame Skip Rate: {frame_skip} (every {frame_skip}th frame)")
    logger.info(f"🎯 Accident Threshold: {accident_threshold} detections")

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video: {video_path}")
        return None

    # Get video info
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"📊 Video Info: {total_frames} frames, {fps:.1f} FPS, Duration: {total_frames/fps:.1f}s")

    # Processing variables
    frame_count = 0
    processed_frames = 0
    accident_detections = []
    confidence_scores = []
    vehicle_counts = []

    logger.info("🚀 Starting efficient video processing...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # FRAME SKIPPING OPTIMIZATION
        if frame_count % frame_skip != 0:
            continue

        processed_frames += 1

        # PERFORMANCE OPTIMIZATION: Resize frame
        frame_resized = cv2.resize(frame, (640, 480))

        # SIMULATE VEHICLE DETECTION (replace with YOLO)
        # Random vehicle count for demo (0-5 vehicles)
        vehicle_count = np.random.randint(0, 6)

        # Skip frames with no vehicles
        if vehicle_count == 0:
            continue

        logger.info(f"🔍 Frame {frame_count}: {vehicle_count} vehicles detected")

        # SIMULATE ACCIDENT ANALYSIS
        # Accident if 3+ vehicles detected (simple logic for demo)
        is_accident = vehicle_count >= 3

        if is_accident:
            confidence = 0.8 + np.random.random() * 0.2  # 0.8-1.0 confidence

            accident_data = {
                'frame_number': frame_count,
                'vehicle_count': vehicle_count,
                'confidence': confidence,
                'timestamp': frame_count / fps
            }

            accident_detections.append(accident_data)
            confidence_scores.append(confidence)
            vehicle_counts.append(vehicle_count)

            logger.info(f"🚨 ACCIDENT DETECTED at frame {frame_count}!")
            logger.info(f"   📊 Vehicles: {vehicle_count}, Confidence: {confidence:.2f}")

    cap.release()

    # VIDEO-LEVEL DECISION MAKING
    logger.info("\n📈 ANALYSIS COMPLETE")
    logger.info(f"   Total frames in video: {total_frames}")
    logger.info(f"   Frames processed: {processed_frames} ({processed_frames/total_frames*100:.1f}%)")
    logger.info(f"   Accident detections: {len(accident_detections)}")

    # FINAL DECISION
    accident_detected = len(accident_detections) >= accident_threshold

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
            'description': f"Accident confirmed with {len(accident_detections)} detections"
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
            'description': "No accident detected"
        }

        logger.info("\n✅ FINAL RESULT: NO ACCIDENT DETECTED")
        logger.info(f"   🎬 Video ID: {video_id}")

    logger.info("="*60)
    return result

def main():
    """Main demo function"""
    print("🚗 Optimized Video-Level Accident Detection Demo")
    print("=" * 50)

    # Option 1: Use existing video
    video_path = "sample_video.mp4"

    # Option 2: Create sample video (uncomment if needed)
    if not os.path.exists(video_path):
        print("Creating sample video for demo...")
        create_sample_video(video_path, duration_seconds=5)

    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        print("Please provide a valid video file path or uncomment the create_sample_video() call")
        return

    # Run optimized processing
    result = optimized_video_processing_demo(
        video_path=video_path,
        frame_skip=5,      # Process every 5th frame (4x speedup)
        accident_threshold=2  # Need 2+ detections to confirm accident
    )

    if result:
        print("\n📋 SUMMARY:")
        print(f"   Video ID: {result['video_id']}")
        print(f"   Accident: {'YES' if result['accident_detected'] else 'NO'}")
        print(f"   Confidence: {result['final_confidence']:.2f}")
        print(f"   Alert Sent: {'YES' if result['alert_sent'] else 'NO'}")

if __name__ == "__main__":
    main()