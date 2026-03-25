"""
Video processing utilities for extracting and preprocessing frames.
"""
import cv2
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Handles video file loading and frame extraction.
    
    This class provides utilities to:
    - Load video files
    - Extract frames
    - Preprocess frames for YOLO detection
    - Handle video metadata
    """
    
    def __init__(self, video_path, target_width=640, target_height=480):
        """
        Initialize video processor.
        
        Args:
            video_path (str): Path to video file
            target_width (int): Target frame width for resizing
            target_height (int): Target frame height for resizing
        """
        self.video_path = video_path
        self.target_width = target_width
        self.target_height = target_height
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.frame_width = 0
        self.frame_height = 0
        
        logger.info(f"Initializing VideoProcessor for: {video_path}")
    
    def open_video(self):
        """
        Open video file and extract metadata.
        
        Returns:
            bool: True if video opened successfully, False otherwise
        """
        try:
            if not os.path.exists(self.video_path):
                logger.error(f"Video file not found: {self.video_path}")
                return False
            
            self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video: {self.video_path}")
                return False
            
            # Extract video metadata
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Video opened successfully")
            logger.info(f"Total frames: {self.total_frames}, FPS: {self.fps}")
            logger.info(f"Original resolution: {self.frame_width}x{self.frame_height}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error opening video: {str(e)}")
            return False
    
    def read_frame(self):
        """
        Read next frame from video.
        
        Returns:
            tuple: (success, frame, frame_number)
                - success: bool indicating if frame was read
                - frame: numpy array of frame (or None if failed)
                - frame_number: current frame number
        """
        if self.cap is None:
            logger.error("Video not opened")
            return False, None, 0
        
        success, frame = self.cap.read()
        frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        
        if not success:
            logger.debug(f"End of video reached")
            return False, None, frame_number
        
        return True, frame, frame_number
    
    def preprocess_frame(self, frame):
        """
        Preprocess frame for YOLO detection.
        
        Args:
            frame (numpy array): Input frame from video
        
        Returns:
            numpy array: Preprocessed frame
        """
        try:
            # Resize frame to target dimensions
            resized_frame = cv2.resize(frame, (self.target_width, self.target_height))
            
            # Normalize frame (optional, but helps with detection)
            # Frame values should be in 0-255 range for YOLO
            
            return resized_frame
        
        except Exception as e:
            logger.error(f"Error preprocessing frame: {str(e)}")
            return None
    
    def save_frame(self, frame, output_path):
        """
        Save frame as image file.
        
        Args:
            frame (numpy array): Frame to save
            output_path (str): Path where frame should be saved
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            success = cv2.imwrite(output_path, frame)
            
            if success:
                logger.debug(f"Frame saved: {output_path}")
            else:
                logger.error(f"Failed to save frame: {output_path}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error saving frame: {str(e)}")
            return False
    
    def close_video(self):
        """Close video file."""
        if self.cap is not None:
            self.cap.release()
            logger.info("Video closed")
    
    def get_video_info(self):
        """
        Get video metadata.
        
        Returns:
            dict: Video information
        """
        return {
            'total_frames': self.total_frames,
            'fps': self.fps,
            'frame_width': self.frame_width,
            'frame_height': self.frame_height,
            'duration_seconds': self.total_frames / self.fps if self.fps > 0 else 0,
        }
    
    def __del__(self):
        """Cleanup: ensure video is closed."""
        self.close_video()
