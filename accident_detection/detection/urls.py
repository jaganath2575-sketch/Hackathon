"""
URL configuration for detection app.
"""
from django.urls import path
from . import views

app_name = 'detection'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('accidents/', views.accidents_list, name='accidents_list'),
    path('accident/<int:accident_id>/', views.accident_detail, name='accident_detail'),
    
    # Video processing
    path('upload/', views.upload_video, name='upload_video'),
    path('process/<int:video_session_id>/', views.process_video, name='process_video'),
    path('status/<int:video_session_id>/', views.video_status, name='video_status'),
    
    # Test/Demo
    path('test/create-accident/', views.test_create_accident, name='test_create_accident'),
    
    # Analytics
    path('statistics/', views.statistics, name='statistics'),
    path('about/', views.about, name='about'),
]
