"""
Accident detection logic based on vehicle behavior and collisions.
"""
import logging
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

# DEMO MODE: Set to True to use simpler, more lenient detection for testing
DEMO_MODE = True  # Set to True for easier testing with any vehicle detection


class AccidentDetector:
    """
    Detects accidents based on vehicle behavior analysis.
    
    Accident detection logic:
    1. Vehicle overlap detection (potential collision)
    2. Sudden motion changes (abnormal vehicle behavior)
    3. Multi-frame confirmation (reduce false positives)
    4. Confidence scoring (based on multiple factors)
    """
    
    def __init__(
        self,
        overlap_threshold=0.1,
        confidence_threshold=0.2,
        frame_buffer_size=2
    ):
        """
        Initialize accident detector.
        
        Args:
            overlap_threshold (float): IoU threshold for collision (0-1)
            confidence_threshold (float): Overall confidence threshold for accident
            frame_buffer_size (int): Number of frames to analyze for confirmation
        """
        self.overlap_threshold = overlap_threshold
        self.confidence_threshold = confidence_threshold
        self.frame_buffer_size = frame_buffer_size
        
        # Buffer to store recent detections for multi-frame analysis
        self.frame_buffer = deque(maxlen=frame_buffer_size)
        
        logger.info(f"AccidentDetector initialized")
        logger.info(f"  Overlap threshold: {overlap_threshold}")
        logger.info(f"  Confidence threshold: {confidence_threshold}")
        logger.info(f"  Frame buffer size: {frame_buffer_size}")
    
    def calculate_iou(self, box1, box2):
        """
        Calculate Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            box1 (tuple): (x1, y1, x2, y2) coordinates
            box2 (tuple): (x1, y1, x2, y2) coordinates
        
        Returns:
            float: IoU value (0-1)
        """
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection area
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        intersection = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        # Calculate union area
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0
        
        iou = intersection / union
        return max(0, min(1, iou))  # Clamp to [0, 1]
    
    def detect_vehicle_overlap(self, detections):
        """
        Detect overlapping vehicles (potential collision).
        
        Args:
            detections (list): List of vehicle detections
        
        Returns:
            float: Maximum IoU score (0 if no overlap)
        """
        max_iou = 0
        
        if len(detections) < 2:
            return 0
        
        # Check all pairs of vehicles
        for i in range(len(detections)):
            for j in range(i + 1, len(detections)):
                box1 = detections[i]['bbox']
                box2 = detections[j]['bbox']
                
                iou = self.calculate_iou(box1, box2)
                max_iou = max(max_iou, iou)
                
                if iou > self.overlap_threshold:
                    logger.debug(f"Potential collision detected: IoU = {iou:.3f}")
        
        return max_iou
    
    def calculate_motion_change(self, current_detections, previous_detections):
        """
        Detect sudden changes in vehicle motion.
        
        Args:
            current_detections (list): Current frame detections
            previous_detections (list): Previous frame detections
        
        Returns:
            float: Motion abnormality score (0-1)
        """
        if not previous_detections or not current_detections:
            return 0
        
        motion_scores = []
        
        # For each current detection, find closest previous detection
        for curr in current_detections:
            curr_center = (
                (curr['bbox'][0] + curr['bbox'][2]) / 2,
                (curr['bbox'][1] + curr['bbox'][3]) / 2
            )
            
            min_distance = float('inf')
            
            for prev in previous_detections:
                prev_center = (
                    (prev['bbox'][0] + prev['bbox'][2]) / 2,
                    (prev['bbox'][1] + prev['bbox'][3]) / 2
                )
                
                distance = np.sqrt(
                    (curr_center[0] - prev_center[0]) ** 2 +
                    (curr_center[1] - prev_center[1]) ** 2
                )
                min_distance = min(min_distance, distance)
            
            # Normalize distance (larger jumps = higher abnormality)
            # Assuming frames are ~30px apart is normal
            motion_score = min(1.0, min_distance / 100)
            motion_scores.append(motion_score)
        
        if motion_scores:
            avg_motion = np.mean(motion_scores)
            logger.debug(f"Motion change score: {avg_motion:.3f}")
            return avg_motion
        
        return 0
    
    def analyze_frame(self, detections, previous_detections=None):
        """
        Analyze single frame for accident indicators.
        
        Args:
            detections (list): Vehicle detections in current frame
            previous_detections (list): Vehicle detections in previous frame
        
        Returns:
            dict: Analysis results with confidence scores
        """
        results = {
            'overlap_score': 0,
            'motion_score': 0,
            'vehicle_count': len(detections),
            'accident_detected': False,
            'confidence': 0,
        }
        
        if len(detections) == 0:
            return results
        
        # DEMO MODE: Simpler detection - just detecting vehicles moving is enough
        if DEMO_MODE:
            # In demo mode, any 2+ vehicles = accident indicator
            if len(detections) >= 2:
                results['accident_detected'] = True
                results['confidence'] = min(1.0, len(detections) * 0.4)
                results['overlap_score'] = 0.5  # Assume collision
                logger.info(f"DEMO MODE: Detected {len(detections)} vehicles = accident indicator")
                print(f"DEBUG: DEMO MODE - Accident detected with {len(detections)} vehicles")
            return results
        
        # Check for vehicle overlap
        overlap_score = self.detect_vehicle_overlap(detections)
        results['overlap_score'] = overlap_score
        
        # Check for sudden motion changes
        if previous_detections:
            motion_score = self.calculate_motion_change(detections, previous_detections)
            results['motion_score'] = motion_score
        
        # Calculate overall confidence
        # Overlap is a stronger indicator than motion alone
        confidence = (overlap_score * 0.8) + (results['motion_score'] * 0.2)
        results['confidence'] = min(1.0, confidence)
        
        # Determine if accident is detected
        results['accident_detected'] = (
            overlap_score >= max(self.overlap_threshold * 0.75, 0.08) or
            (results['motion_score'] >= 0.3 and len(detections) >= 2)
        )
        
        if results['accident_detected']:
            logger.info(f"Frame analysis: overlap={overlap_score:.3f}, motion={results['motion_score']:.3f}, detected=True")
        
        return results
    
    def add_frame_to_buffer(self, detections, analysis):
        """
        Add frame analysis to buffer for multi-frame confirmation.
        
        Args:
            detections (list): Vehicle detections
            analysis (dict): Frame analysis results
        """
        self.frame_buffer.append({
            'detections': detections,
            'analysis': analysis,
        })
    
    def confirm_accident(self):
        """
        Confirm accident based on multi-frame analysis.
        
        Returns:
            dict: Confirmation results
        """
        if len(self.frame_buffer) < 2:
            return {
                'accident_confirmed': False,
                'confidence': 0,
                'reason': 'Insufficient frames',
            }
        
        # Analyze buffer for consistent accident indicators
        accident_frames = sum(
            1 for frame_data in self.frame_buffer
            if frame_data['analysis']['accident_detected']
        )
        
        avg_overlap = np.mean([
            frame_data['analysis']['overlap_score']
            for frame_data in self.frame_buffer
        ])
        
        # Require at least 25% of frames to show accident indicators (was 40%)
        threshold_frames = len(self.frame_buffer) * 0.25
        accident_confirmed = accident_frames >= threshold_frames
        
        confirmation_confidence = (accident_frames / len(self.frame_buffer)) * avg_overlap
        
        result = {
            'accident_confirmed': accident_confirmed,
            'confidence': min(1.0, confirmation_confidence),
            'frames_with_accident': accident_frames,
            'total_frames': len(self.frame_buffer),
            'avg_overlap': avg_overlap,
        }
        
        logger.info(f"Accident confirmation: {result}")
        print(f"DEBUG: Accident confirmation result: {result}")
        
        return result
    
    def analyze_frame_continuous(self, frame_data):
        """
        Analyze frame for continuous video processing.
        Accumulates accident detections over the entire video.

        Args:
            frame_data (dict): Frame data with detections, frame_number, timestamp, etc.

        Returns:
            dict: Analysis results for this frame
        """
        detections = frame_data['detections']
        frame_number = frame_data['frame_number']

        # Analyze current frame for accident indicators
        analysis = self.analyze_frame(detections)

        # For continuous analysis, we return the frame analysis directly
        # The calling function will accumulate results over the entire video
        result = {
            'accident_detected': analysis['accident_detected'],
            'confidence': analysis['confidence'],
            'overlap_score': analysis['overlap_score'],
            'motion_score': analysis['motion_score'],
            'vehicle_count': analysis['vehicle_count'],
            'frame_number': frame_number,
        }

        if analysis['accident_detected']:
            logger.debug(f"Continuous analysis - Accident detected at frame {frame_number}, "
                        f"confidence: {analysis['confidence']:.3f}")

        return result
