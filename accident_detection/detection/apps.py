"""
App configuration for detection app.
"""
from django.apps import AppConfig


class DetectionConfig(AppConfig):
    """Configuration class for the detection app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detection'
    verbose_name = 'Accident Detection System'
