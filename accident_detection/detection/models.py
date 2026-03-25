"""
Database models for accident detection system.
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Accident(models.Model):
    """
    Model to store detected accident records.
    
    Attributes:
        id: Unique identifier (auto-generated)
        timestamp: Time when accident was detected (system time)
        location: Location/camera ID where accident occurred
        video_id: Reference to the video file being processed
        image: Captured frame showing the accident
        confidence_score: Detection confidence (0-100)
        vehicle_count: Number of vehicles involved
        description: Additional details about the accident
        is_confirmed: Whether accident was confirmed with multi-frame analysis
        accident_time: Timestamp in video when accident first occurred (HH:MM:SS format)
        created_at: Record creation timestamp
    """
    
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    location = models.CharField(max_length=100, default="Road - Unknown")
    video_id = models.CharField(max_length=100, default="video_001")
    image = models.ImageField(
        upload_to='accident_images/%Y/%m/%d/',
        help_text='Captured frame of the accident'
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text='Detection confidence percentage (0-100)'
    )
    vehicle_count = models.IntegerField(default=1, help_text='Number of vehicles detected')
    description = models.TextField(blank=True, null=True, help_text='Additional details')
    is_confirmed = models.BooleanField(
        default=False,
        help_text='Confirmed after multi-frame analysis'
    )
    accident_time = models.CharField(
        max_length=12,
        default="00:00:00",
        help_text='Timestamp in video (HH:MM:SS format)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Accident Record'
        verbose_name_plural = 'Accident Records'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        """Return string representation of accident."""
        return f"Accident at {self.location} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def get_confidence_percentage(self):
        """Return confidence as a readable percentage."""
        return f"{self.confidence_score:.2f}%"


class VideoSession(models.Model):
    """
    Model to track video processing sessions.
    
    Attributes:
        id: Unique session identifier
        video_file: Path to uploaded video
        filename: Original video filename
        location: Location/camera ID where video was recorded
        video_id: Unique video identifier
        total_frames: Total frames in video
        processed_frames: Frames processed so far
        status: Current processing status
        start_time: When processing started
        end_time: When processing ended
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('detected', 'Accident Detected'),
        ('not_detected', 'No Accident Detected'),
        ('failed', 'Failed'),
    ]
    
    id = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=255, help_text='Original video filename')
    video_file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    location = models.CharField(max_length=100, default="Road - Unknown", help_text='Camera location or road name')
    video_id = models.CharField(max_length=100, default="video_001", help_text='Unique video identifier')
    total_frames = models.IntegerField(default=0)
    processed_frames = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_processed = models.BooleanField(default=False, help_text='Whether video has been processed')
    alert_sent = models.BooleanField(default=False, help_text='Whether alert has been sent')
    accident_detected = models.BooleanField(default=False, help_text='Whether accident was detected in video')
    first_accident_time = models.CharField(
        max_length=12,
        default="00:00:00",
        help_text='Time of first detected accident in video (HH:MM:SS)'
    )
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Video Session'
        verbose_name_plural = 'Video Sessions'
    
    def __str__(self):
        """Return string representation of video session."""
        return f"Video: {self.filename} - Status: {self.status}"
    
    def get_progress_percentage(self):
        """Calculate processing progress percentage."""
        if self.total_frames == 0:
            return 0
        return (self.processed_frames / self.total_frames) * 100
