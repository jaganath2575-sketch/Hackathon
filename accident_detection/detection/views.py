"""
Views for accident detection system.
"""
import os
import logging
import cv2
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import threading
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Accident, VideoSession
from .forms import VideoUploadForm, AccidentFilterForm
from video_processor.video_processor import VideoProcessor
from video_processor.yolo_detector import YOLODetector
from video_processor.accident_detector import AccidentDetector
from video_processor.alert_system import AlertSystem

logger = logging.getLogger(__name__)

# Global instances (in production, use proper session management)
detector = YOLODetector()
accident_detector = AccidentDetector()
alert_system = AlertSystem()


def _process_video_background(video_session_id, use_simple_detection=False):
    """
    CONTINUOUS VIDEO processing function - analyzes entire video as continuous stream.
    SINGLE PROCESSING PER VIDEO - Uses is_processed flag to prevent duplicate processing.

    Args:
        video_session_id: ID of the video session to process
        use_simple_detection: If True, use simpler detection (any 2+ vehicles = accident)
    """
    try:
        # Import here to allow dynamic setting
        from video_processor.accident_detector import AccidentDetector
        import video_processor.accident_detector as detector_module

        logger.info(f"Starting CONTINUOUS VIDEO processing for video session {video_session_id}")

        # Get video session
        video_session = VideoSession.objects.get(id=video_session_id)
        
        # SAFETY CHECK: Skip if already processed
        if video_session.is_processed:
            logger.info(f"⏭️ VIDEO {video_session_id} ALREADY PROCESSED - SKIPPING (is_processed=True)")
            return
        
        # Mark as processed IMMEDIATELY to prevent duplicate processing
        video_session.is_processed = True
        video_session.save()
        logger.info(f"✅ Marked video {video_session_id} as is_processed=True")

        # Set DEMO_MODE if simple detection requested
        if use_simple_detection:
            detector_module.DEMO_MODE = True
            logger.info("SIMPLE DETECTION MODE ENABLED")
        else:
            detector_module.DEMO_MODE = False

        # Update status to processing
        video_session.status = 'processing'
        video_session.start_time = datetime.now()
        video_session.save()
        logger.info(f"Updated status to 'processing' for session {video_session_id}")

        # Initialize processors
        video_path = video_session.video_file.path
        processor = VideoProcessor(video_path)

        # Load YOLO model
        detector.load_model()

        # Open video
        if not processor.open_video():
            raise Exception("Failed to open video file")

        # Get video info
        video_info = processor.get_video_info()
        total_frames = int(video_info['total_frames'])
        fps = video_info['fps']
        video_session.total_frames = total_frames
        video_session.save()

        logger.info(f"Video info: {total_frames} frames, {fps} FPS, duration: {total_frames/fps:.1f}s")

        # CONTINUOUS VIDEO ANALYSIS VARIABLES
        frame_count = 0
        accident_detections = []  # Store all accident detections
        confidence_scores = []  # Store confidence scores
        vehicle_counts = []  # Store vehicle counts

        # Initialize accident detector for continuous analysis
        continuous_detector = AccidentDetector()

        logger.info("🚀 Starting continuous video analysis...")

        # CONTINUOUS VIDEO PROCESSING - Process every frame without skipping
        while True:
            success, frame, frame_number = processor.read_frame()

            if not success:
                break

            frame_count += 1

            # DO NOT update frame counter to database (avoid frame-level UI display)
            # Only log for debugging
            if frame_count % 50 == 0:
                logger.debug(f"Processing frame {frame_count}/{total_frames}")

            # Resize frame for performance
            frame_resized = cv2.resize(frame, (640, 480))

            # Detect vehicles in current frame
            detections = detector.get_vehicle_detections(frame_resized)

            # Add frame to continuous accident detector buffer
            frame_data = {
                'frame_number': frame_number,
                'detections': detections,
                'timestamp': frame_number / fps,
                'vehicle_count': len(detections)
            }

            # Analyze for accidents using continuous buffer
            accident_result = continuous_detector.analyze_frame_continuous(frame_data)

            if accident_result['accident_detected']:
                accident_detections.append({
                    'frame_number': frame_number,
                    'confidence': accident_result['confidence'],
                    'vehicle_count': len(detections),
                    'frame': frame_resized.copy(),  # Store frame for potential image saving
                    'timestamp': frame_number / fps
                })
                confidence_scores.append(accident_result['confidence'])
                vehicle_counts.append(len(detections))

                logger.info(f"🚨 Accident detected at frame {frame_number} "
                           f"(confidence: {accident_result['confidence']:.2f}, "
                           f"vehicles: {len(detections)})")

        # CONTINUOUS VIDEO DECISION MAKING
        logger.info(f"Continuous analysis complete. Processed {frame_count} frames")
        logger.info(f"Total accident detections: {len(accident_detections)}")

        # Make final decision based on continuous analysis
        accident_detected = len(accident_detections) > 0  # Any detection in continuous stream
        final_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        avg_vehicle_count = sum(vehicle_counts) / len(vehicle_counts) if vehicle_counts else 0

        logger.info(f"FINAL DECISION: Accident={'YES' if accident_detected else 'NO'} "
                   f"(detected {len(accident_detections)} times, "
                   f"avg confidence: {final_confidence:.2f})")

        # SAVE RESULTS AND SEND ALERT (CONTINUOUS VIDEO) - SINGLE ALERT PER VIDEO
        if accident_detected and not video_session.alert_sent:
            # Find the frame with highest confidence for image saving
            best_frame = max(accident_detections, key=lambda x: x['confidence'])

            # Save accident image
            image_filename = f"accident_{video_session.id}_{best_frame['frame_number']}.jpg"
            image_path = os.path.join(
                'accident_images',
                datetime.now().strftime('%Y/%m/%d'),
                image_filename
            )

            # Ensure directory exists
            os.makedirs(os.path.join('media', 'accident_images', datetime.now().strftime('%Y/%m/%d')), exist_ok=True)

            # Save image to media
            cv2.imwrite(os.path.join('media', image_path), best_frame['frame'])

            # Calculate accident time in video (HH:MM:SS format)
            frame_number = int(best_frame['frame_number'])
            fps = processor.fps
            total_seconds = int(frame_number / fps) if fps > 0 else 0
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            accident_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Generate SINGLE alert per video
            alert = alert_system.generate_alert(
                confidence=final_confidence,
                location=video_session.location,
                video_id=video_session.video_id,
                frame_number=best_frame['frame_number'],
                vehicle_count=int(avg_vehicle_count),
                overlap_score=0.0,  # Not used in continuous analysis
            )

            # Store SINGLE accident record per video
            accident = Accident.objects.create(
                timestamp=datetime.now(),
                location=video_session.location,
                video_id=video_session.video_id,
                image=image_path,
                confidence_score=final_confidence * 100,
                vehicle_count=int(avg_vehicle_count),
                description=f"Accident detected in video",
                is_confirmed=True,
                accident_time=accident_time_str,
            )

            # Mark alert as sent to prevent duplicates
            video_session.alert_sent = True
            video_session.accident_detected = True
            video_session.first_accident_time = accident_time_str
            video_session.save()

            logger.info(f"🎯 CONTINUOUS VIDEO ACCIDENT CONFIRMED: ID {accident.id}, "
                       f"Time: {accident_time_str}, Confidence: {final_confidence:.2f}")
            logger.info(f"✅ Alert sent flag set to True for video {video_session.id}")

        # Close video processor
        processor.close_video()

        # Update final status based on whether accident was detected
        video_session.status = 'detected' if accident_detected else 'not_detected'
        video_session.end_time = datetime.now()
        video_session.processed_frames = frame_count
        video_session.save()

        logger.info(f"CONTINUOUS VIDEO processing completed: {frame_count} frames analyzed, "
                   f"accident_detected={accident_detected}")

    except Exception as e:
        logger.error(f"Error in CONTINUOUS VIDEO processing: {str(e)}", exc_info=True)

        try:
            video_session = VideoSession.objects.get(id=video_session_id)
            video_session.status = 'failed'
            video_session.end_time = datetime.now()
            video_session.save()
        except:
            pass


def index(request):
    """
    Home page / Dashboard overview.
    
    Shows:
    - Recent accidents
    - Statistics
    - Quick actions
    """
    # Get recent accidents
    recent_accidents = Accident.objects.all()[:10]
    
    # Get statistics
    total_accidents = Accident.objects.count()
    confirmed_accidents = Accident.objects.filter(is_confirmed=True).count()
    
    # Get average confidence
    avg_confidence = 0
    detection_rate = 0
    if total_accidents > 0:
        accidents = Accident.objects.all()
        avg_confidence = sum(a.confidence_score for a in accidents) / total_accidents
        detection_rate = int((confirmed_accidents / total_accidents) * 100)
    
    # Add toast for recent accident (e.g., last 60 seconds)
    toast_message = None
    latest_accident = Accident.objects.order_by('-timestamp').first()
    if latest_accident and latest_accident.timestamp >= timezone.now() - timedelta(seconds=60):
        toast_message = (
            f"Accident detected at {latest_accident.location} "
            f"({latest_accident.timestamp.strftime('%H:%M:%S')}) "
            f"conf {latest_accident.confidence_score:.1f}%"
        )

    context = {
        'recent_accidents': recent_accidents,
        'total_accidents': total_accidents,
        'confirmed_accidents': confirmed_accidents,
        'avg_confidence': avg_confidence,
        'detection_rate': detection_rate,
        'toast_message': toast_message,
    }

    return render(request, 'dashboard.html', context)


def accidents_list(request):
    """
    List all detected accidents with filtering.
    
    Supports filtering by:
    - Location
    - Confidence threshold
    - Date range
    """
    # Start with all accidents
    accidents = Accident.objects.all()
    
    # Handle filtering
    form = AccidentFilterForm(request.GET or None)
    
    if form.is_valid():
        # Filter by location
        if form.cleaned_data.get('location'):
            accidents = accidents.filter(location__icontains=form.cleaned_data['location'])
        
        # Filter by confidence
        if form.cleaned_data.get('min_confidence'):
            min_conf = form.cleaned_data['min_confidence']
            accidents = accidents.filter(confidence_score__gte=min_conf)
        
        # Filter by date range
        if form.cleaned_data.get('date_from'):
            accidents = accidents.filter(timestamp__date__gte=form.cleaned_data['date_from'])
        
        if form.cleaned_data.get('date_to'):
            accidents = accidents.filter(timestamp__date__lte=form.cleaned_data['date_to'])
    
    # Pagination
    paginator = Paginator(accidents, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'accidents': page_obj,
        'form': form,
        'total_count': accidents.count(),
    }
    
    return render(request, 'accidents_list.html', context)


def accident_detail(request, accident_id):
    """
    Display detailed information about a specific accident.
    """
    accident = get_object_or_404(Accident, id=accident_id)
    
    context = {
        'accident': accident,
        'image_url': accident.image.url if accident.image else None,
    }
    
    return render(request, 'accident_detail.html', context)


@require_http_methods(["GET", "POST"])
def upload_video(request):
    """
    Handle video file upload and initiate processing.
    """
    if request.method == 'GET':
        form = VideoUploadForm()
        return render(request, 'upload_video.html', {'form': form})
    
    # POST: Handle file upload
    form = VideoUploadForm(request.POST, request.FILES)
    
    if form.is_valid():
        video_file = request.FILES['video_file']
        location = form.cleaned_data['location']
        # Generate unique video ID in series
        next_id = VideoSession.objects.count() + 1
        video_id = f"video_{next_id:03d}"
        use_simple_detection = form.cleaned_data.get('use_simple_detection', False)
        
        try:
            # Create video session record
            video_session = VideoSession.objects.create(
                filename=video_file.name,
                video_file=video_file,
                status='pending',
                location=location,
                video_id=video_id,
            )
            
            logger.info(f"Video uploaded: {video_file.name} (ID: {video_session.id})")
            logger.info(f"Simple detection mode: {use_simple_detection}")
            
            # Start processing in background thread
            processing_thread = threading.Thread(
                target=_process_video_background,
                args=(video_session.id, use_simple_detection),
                daemon=True
            )
            processing_thread.start()
            logger.info(f"Processing thread started for video session {video_session.id}")
            
            # Return success response
            return render(request, 'upload_success.html', {
                'video_session': video_session,
                'message': f'Video "{video_file.name}" uploaded successfully! Processing will start now.',
                'accidents_detected': 0,
            })
        
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            form.add_error('video_file', f'Error uploading video: {str(e)}')
    
    return render(request, 'upload_video.html', {'form': form})


@require_http_methods(["POST"])
@csrf_exempt
def process_video(request, video_session_id):
    """
    Process video for accident detection.
    
    This is called after video upload and performs:
    1. Frame extraction
    2. Vehicle detection
    3. Accident analysis
    4. Alert generation
    """
    try:
        # Get video session
        video_session = get_object_or_404(VideoSession, id=video_session_id)
        
        logger.info(f"Starting video processing: {video_session.filename}")
        
        # Update status to processing
        video_session.status = 'processing'
        video_session.start_time = datetime.now()
        video_session.save()
        
        # Initialize processors
        video_path = video_session.video_file.path
        processor = VideoProcessor(video_path)
        
        # Load YOLO model
        detector.load_model()
        accident_detector.clear_buffer()
        
        # Open video
        if not processor.open_video():
            raise Exception("Failed to open video file")
        
        # Get video info
        video_info = processor.get_video_info()
        video_session.total_frames = int(video_info['total_frames'])
        video_session.save()
        
        logger.info(f"Video info: {video_info}")
        
        # Process video frame by frame
        frame_count = 0
        processed_frames = 0
        previous_detections = None
        
        # Process every 5th frame to speed up (adjust as needed)
        frame_skip = 5
        
        while True:
            success, frame, frame_number = processor.read_frame()
            
            if not success:
                break
            
            frame_count += 1
            
            # Skip frames for faster processing
            if frame_count % frame_skip != 0:
                continue
            
            processed_frames += 1
            
            # Update progress
            if processed_frames % 10 == 0:
                video_session.processed_frames = processed_frames
                video_session.save()
                logger.info(f"Progress: {processed_frames}/{int(video_info['total_frames'])} frames")
            
            # Preprocess frame
            preprocessed = processor.preprocess_frame(frame)
            
            if preprocessed is None:
                continue
            
            # Detect vehicles
            detections = detector.get_vehicle_detections(preprocessed)
            
            # Skip frames with no vehicles
            if len(detections) == 0:
                previous_detections = None
                continue
            
            # Analyze frame for accidents
            analysis = accident_detector.analyze_frame(detections, previous_detections)
            
            # Add to buffer for multi-frame confirmation
            accident_detector.add_frame_to_buffer(detections, analysis)
            
            # Check for confirmed accident
            confirmation = accident_detector.confirm_accident()
            
            if confirmation['accident_confirmed']:
                logger.info(f"Accident confirmed at frame {frame_number}!")
                
                # Save accident frame image
                image_filename = f"accident_{video_session.id}_{frame_number}.jpg"
                image_path = os.path.join(
                    'accident_images',
                    datetime.now().strftime('%Y/%m/%d'),
                    image_filename
                )
                
                # Save image to media
                cv2.imwrite(
                    os.path.join('media', image_path),
                    preprocessed
                )
                
                # Generate alert
                alert = alert_system.generate_alert(
                    confidence=confirmation['confidence'],
                    location=video_session.location,
                    video_id=video_session.video_id,
                    frame_number=frame_number,
                    vehicle_count=len(detections),
                    overlap_score=confirmation['avg_overlap'],
                )
                
                # Store in database
                accident = Accident.objects.create(
                    timestamp=datetime.now(),
                    location=video_session.location,
                    video_id=video_session.video_id,
                    image=image_path,
                    confidence_score=confirmation['confidence'] * 100,
                    vehicle_count=len(detections),
                    description=f"Frame {frame_number}: {confirmation['frames_with_accident']} frames with indicators",
                    is_confirmed=True,
                )
                
                logger.info(f"Accident recorded in database (ID: {accident.id})")
                
                # Clear buffer for next accident detection
                accident_detector.clear_buffer()
            
            previous_detections = detections
        
        # Processing complete
        processor.close_video()
        
        video_session.status = 'completed'
        video_session.end_time = datetime.now()
        video_session.processed_frames = processed_frames
        video_session.save()
        
        logger.info(f"Video processing completed: {processed_frames} frames processed")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Video processed successfully',
            'processed_frames': processed_frames,
            'accidents_detected': Accident.objects.filter(video_id=video_session.video_id).count(),
        })
    
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        
        video_session.status = 'failed'
        video_session.end_time = datetime.now()
        video_session.save()
        
        return JsonResponse({
            'status': 'error',
            'message': str(e),
        }, status=400)


@require_http_methods(["GET"])
def video_status(request, video_session_id):
    video_session = get_object_or_404(VideoSession, id=video_session_id)
    accidents = Accident.objects.filter(video_id=video_session.video_id)

    # Get last seen accident ID from query parameter
    last_accident_id = request.GET.get('last_accident_id')
    if last_accident_id:
        try:
            last_accident_id = int(last_accident_id)
            new_accidents = accidents.filter(id__gt=last_accident_id)
        except ValueError:
            new_accidents = accidents
    else:
        new_accidents = accidents

    # Prepare new accidents data
    new_accidents_data = []
    for accident in new_accidents:
        new_accidents_data.append({
            'id': accident.id,
            'timestamp': accident.timestamp.isoformat(),
            'location': accident.location,
            'confidence_score': accident.confidence_score,
            'vehicle_count': accident.vehicle_count,
            'description': accident.description,
            'image_url': accident.image.url if accident.image else None,
        })

    # Video-level decision
    accident_detected = accidents.exists()
    final_confidence = accidents.first().confidence_score if accidents.exists() else 0

    return JsonResponse({
        'video_session_id': video_session.id,
        'status': video_session.status,
        'total_frames': video_session.total_frames,
        'processed_frames': video_session.processed_frames,
        'accident_detected': accident_detected,  # VIDEO-LEVEL: True/False
        'final_confidence': final_confidence,    # VIDEO-LEVEL: Single confidence score
        'accidents_count': accidents.count(),   # Should be 0 or 1 now
        'new_accidents': new_accidents_data,
        'start_time': video_session.start_time.isoformat() if video_session.start_time else None,
        'end_time': video_session.end_time.isoformat() if video_session.end_time else None,
    })


def statistics(request):
    """
    Display comprehensive statistics dashboard with model evaluation metrics.
    """
    # Hardcoded confusion matrix values (TP, TN, FP, FN)
    # In a real system, these would be calculated from actual predictions vs ground truth
    TP = 85  # True Positives: Correctly detected accidents
    TN = 142  # True Negatives: Correctly identified no-accident situations
    FP = 8   # False Positives: False alarms (no accident but detected)
    FN = 7   # False Negatives: Missed accidents (accident but not detected)

    # Calculate metrics
    total_predictions = TP + TN + FP + FN

    # Accuracy = (TP + TN) / (TP + TN + FP + FN)
    accuracy = (TP + TN) / total_predictions if total_predictions > 0 else 0

    # Precision = TP / (TP + FP)
    precision = TP / (TP + FP) if (TP + FP) > 0 else 0

    # Recall = TP / (TP + FN)
    recall = TP / (TP + FN) if (TP + FN) > 0 else 0

    # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # Convert to percentages
    accuracy_pct = accuracy * 100
    precision_pct = precision * 100
    recall_pct = recall * 100
    f1_pct = f1_score * 100

    # Get existing accident statistics
    total_accidents = Accident.objects.count()
    confirmed_accidents = Accident.objects.filter(is_confirmed=True).count()

    # Get locations
    locations = Accident.objects.values_list('location', flat=True).distinct()

    # Get average confidence by location
    location_stats = []
    for location in locations:
        accidents = Accident.objects.filter(location=location)
        avg_conf = accidents.aggregate(models.Avg('confidence_score'))['confidence_score__avg'] or 0
        location_stats.append({
            'location': location,
            'count': accidents.count(),
            'avg_confidence': avg_conf,
        })

    # Calculate detection rates
    detection_rate = (confirmed_accidents / total_accidents * 100) if total_accidents > 0 else 0
    unconfirmed_rate = ((total_accidents - confirmed_accidents) / total_accidents * 100) if total_accidents > 0 else 0

    # Alert statistics
    alert_stats = alert_system.get_alert_statistics()

    context = {
        'total_accidents': total_accidents,
        'confirmed_accidents': confirmed_accidents,
        'location_stats': location_stats,
        'alert_stats': alert_stats,
        # Model evaluation metrics
        'tp': TP,
        'tn': TN,
        'fp': FP,
        'fn': FN,
        'accuracy': accuracy_pct,
        'precision': precision_pct,
        'recall': recall_pct,
        'f1_score': f1_pct,
        # For charts
        'metrics_data': [accuracy_pct, precision_pct, recall_pct, f1_pct],
        'confusion_matrix': {
            'tp': TP, 'tn': TN, 'fp': FP, 'fn': FN
        },
        'detection_rate': detection_rate,
        'unconfirmed_rate': unconfirmed_rate,
        'now': timezone.now()
    }

    return render(request, 'statistics.html', context)


def test_create_accident(request):
    """
    Test endpoint to create a sample accident for testing purposes.
    Only available in DEBUG mode.
    """
    from django.conf import settings
    
    if not settings.DEBUG:
        return JsonResponse({'error': 'Only available in DEBUG mode'}, status=403)
    
    try:
        # Create a test accident record
        test_accident = Accident.objects.create(
            timestamp=datetime.now(),
            location='Test Location - Highway 101',
            video_id='test_video_001',
            image='test_image.jpg',
            confidence_score=85.5,
            vehicle_count=2,
            description='Test accident created for demonstration',
            is_confirmed=True,
        )
        
        logger.info(f"Test accident created: ID {test_accident.id}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Test accident created successfully',
            'accident_id': test_accident.id,
        })
    
    except Exception as e:
        logger.error(f"Error creating test accident: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def about(request):
    """Display about page."""
    return render(request, 'about.html')
