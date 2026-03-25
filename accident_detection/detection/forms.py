"""
Forms for accident detection system.
"""
from django import forms
from django.core.validators import FileExtensionValidator
from .models import VideoSession


class VideoUploadForm(forms.Form):
    """Form for uploading video files."""
    
    video_file = forms.FileField(
        label='Select Video File',
        help_text='Supported: MP4, AVI, MOV (Max 500MB)',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', 'avi', 'mov', 'mkv', 'flv']
            )
        ]
    )
    
    location = forms.CharField(
        max_length=100,
        initial='Road - Unknown',
        help_text='Camera location or road name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter location name'
        })
    )
    
    video_id = forms.CharField(
        max_length=100,
        required=False,
        help_text='Auto-generated unique video identifier',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'placeholder': 'Auto-generated'
        })
    )
    
    use_simple_detection = forms.BooleanField(
        required=False,
        initial=False,
        label='Use Simple Detection Mode (for testing)',
        help_text='Enable simpler, more lenient accident detection',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class AccidentFilterForm(forms.Form):
    """Form for filtering accident records."""
    
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by location'
        })
    )
    
    min_confidence = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum confidence %'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
