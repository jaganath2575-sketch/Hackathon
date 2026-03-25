"""
YOLO-based vehicle detection module.
"""
import logging
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import YOLOv5
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available")


class YOLODetector:
    """
    Vehicle and object detection using YOLO.
    
    This class handles:
    - Loading YOLO model
    - Running inference on frames
    - Filtering detections for vehicles
    - Extracting bounding boxes and confidence scores
    """
    
    # Vehicle class IDs in COCO dataset
    VEHICLE_CLASSES = {
        2: 'car',
        3: 'motorcycle',
        5: 'bus',
        7: 'truck',
    }
    
    def __init__(self, model_name='yolov5s', confidence_threshold=0.35):
        """
        Initialize YOLO detector.
        
        Args:
            model_name (str): YOLO model name (yolov5s, yolov5m, yolov5l, etc.)
            confidence_threshold (float): Confidence threshold for detections (0-1)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = None
        
        logger.info(f"Initializing YOLO Detector: {model_name}")
    
    def load_model(self):
        """
        Load YOLO model from YOLOv5.
        
        Returns:
            bool: True if model loaded successfully
        """
        try:
            if not TORCH_AVAILABLE:
                logger.error("PyTorch is required for YOLO. Install: pip install torch torchvision")
                return False
            
            # Load YOLOv5 model
            import torch
            self.model = torch.hub.load('ultralytics/yolov5', self.model_name)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.conf = self.confidence_threshold
            
            logger.info(f"YOLO model loaded successfully on {self.device}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading YOLO model: {str(e)}")
            logger.warning("Continuing with fallback object detection")
            return False
    
    def detect_objects(self, frame):
        """
        Detect objects in frame using YOLO.
        
        Args:
            frame (numpy array): Input frame
        
        Returns:
            list: List of detections, each containing:
                {
                    'class_id': int,
                    'class_name': str,
                    'confidence': float,
                    'bbox': (x1, y1, x2, y2)
                }
        """
        if self.model is None:
            logger.warning("Model not loaded, using fallback detection")
            return self._fallback_detection(frame)
        
        try:
            # Run inference
            results = self.model(frame)
            
            # Parse results
            detections = []
            predictions = results.xyxy[0]  # Get predictions (x1, y1, x2, y2, conf, class)
            
            for pred in predictions:
                x1, y1, x2, y2, conf, cls_id = pred.tolist()
                cls_id = int(cls_id)
                
                # Filter for vehicles and common objects
                if cls_id in self.VEHICLE_CLASSES:
                    detections.append({
                        'class_id': cls_id,
                        'class_name': self.VEHICLE_CLASSES[cls_id],
                        'confidence': float(conf),
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    })
                # Also detect person (class 0) as they can be in accidents
                elif cls_id == 0:
                    detections.append({
                        'class_id': cls_id,
                        'class_name': 'person',
                        'confidence': float(conf),
                        'bbox': (int(x1), int(y1), int(x2), int(y2)),
                    })
            
            return detections
        
        except Exception as e:
            logger.error(f"Error during object detection: {str(e)}")
            return []
    
    def _fallback_detection(self, frame):
        """
        Fallback detection method when YOLO is not available.
        Uses basic shape detection and edge detection.
        
        Args:
            frame (numpy array): Input frame
        
        Returns:
            list: List of detected objects
        """
        import cv2
        
        detections = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 100, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area (remove very small detections)
            min_area = 500
            max_area = frame.shape[0] * frame.shape[1] * 0.5
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Estimate confidence based on contour shape
                    circularity = 4 * np.pi * area / (cv2.arcLength(contour, True) ** 2)
                    confidence = min(0.6, circularity)
                    
                    detections.append({
                        'class_id': 2,  # Assume car
                        'class_name': 'vehicle (detected)',
                        'confidence': float(confidence),
                        'bbox': (x, y, x + w, y + h),
                    })
            
            logger.debug(f"Fallback detection found {len(detections)} objects")
            return detections
        
        except Exception as e:
            logger.error(f"Error in fallback detection: {str(e)}")
            return []
    
    def get_vehicle_detections(self, frame):
        """
        Get only vehicle detections from frame.
        
        Args:
            frame (numpy array): Input frame
        
        Returns:
            list: List of vehicle detections
        """
        all_detections = self.detect_objects(frame)
        
        # Filter for vehicles and persons
        vehicle_detections = [
            d for d in all_detections 
            if d['class_id'] in list(self.VEHICLE_CLASSES.keys()) + [0]
        ]
        
        return vehicle_detections
