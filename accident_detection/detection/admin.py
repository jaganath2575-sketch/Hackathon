"""
Admin configuration for accident detection system.
"""
from django.contrib import admin
from .models import Accident, VideoSession


@admin.register(Accident)
class AccidentAdmin(admin.ModelAdmin):
    """Admin interface for Accident model."""
    
    list_display = ('id', 'timestamp', 'location', 'accident_time', 'confidence_score', 'vehicle_count', 'is_confirmed')
    list_filter = ('location', 'is_confirmed', 'timestamp')
    search_fields = ('location', 'description')
    readonly_fields = ('id', 'created_at', 'image')
    fieldsets = (
        ('Incident Information', {
            'fields': ('id', 'timestamp', 'accident_time', 'location', 'video_id')
        }),
        ('Detection Details', {
            'fields': ('confidence_score', 'vehicle_count', 'is_confirmed')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Notes', {
            'fields': ('description',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'timestamp'


@admin.register(VideoSession)
class VideoSessionAdmin(admin.ModelAdmin):
    """Admin interface for VideoSession model."""
    
    list_display = ('id', 'filename', 'status', 'accident_detected', 'first_accident_time', 'processed_frames', 'total_frames', 'created_at')
    list_filter = ('status', 'accident_detected', 'created_at')
    search_fields = ('filename',)
    readonly_fields = ('created_at', 'updated_at', 'processed_frames')
    fieldsets = (
        ('Video Information', {
            'fields': ('filename', 'video_file', 'location', 'video_id')
        }),
        ('Processing Status', {
            'fields': ('status', 'is_processed', 'processed_frames', 'total_frames')
        }),
        ('Accident Detection', {
            'fields': ('accident_detected', 'first_accident_time', 'alert_sent')
        }),
        ('Timeline', {
            'fields': ('start_time', 'end_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'created_at'
