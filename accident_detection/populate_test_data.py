"""
Utility script to populate test data in the database.
Useful for demo and testing purposes.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accident_detection.settings')
django.setup()

from detection.models import Accident, VideoSession
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw
import io


def create_test_image(text="Test Image"):
    """Create a simple test image."""
    img = Image.new('RGB', (640, 480), color='blue')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill='white')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return ContentFile(img_bytes.getvalue(), name='test_image.jpg')


def populate_test_data():
    """Populate database with test accident records."""
    
    print("Creating test data...")
    
    locations = [
        "Highway 101, Exit 5",
        "Main Street & 5th Avenue",
        "Downtown Intersection",
        "Airport Road",
    ]
    
    # Create test accidents
    for i in range(10):
        location = locations[i % len(locations)]
        
        # Create image
        image = create_test_image(f"Accident #{i+1}")
        
        # Create accident record
        accident = Accident.objects.create(
            timestamp=datetime.now() - timedelta(hours=i),
            location=location,
            video_id=f"camera_{(i % 4) + 1:02d}",
            image=image,
            confidence_score=50 + (i % 5) * 10,  # 50-90%
            vehicle_count=2 + (i % 3),  # 2-4 vehicles
            description=f"Test accident #{i+1}. Multiple vehicles involved.",
            is_confirmed=True if i < 8 else False,
        )
        
        print(f"✓ Created: {accident}")
    
    print(f"\n✅ Test data created successfully!")
    print(f"Total accidents: {Accident.objects.count()}")
    
    # Show summary
    from django.db.models import Avg, Count
    stats = Accident.objects.aggregate(
        total=Count('id'),
        avg_confidence=Avg('confidence_score'),
        confirmed=Count('id', filter=models.Q(is_confirmed=True))
    )
    
    print(f"\nStatistics:")
    print(f"- Total: {stats['total']}")
    print(f"- Confirmed: {stats['confirmed']}")
    print(f"- Avg Confidence: {stats['avg_confidence']:.1f}%")


def clear_test_data():
    """Clear all test data from database."""
    
    count = Accident.objects.count()
    Accident.objects.all().delete()
    
    print(f"✓ Deleted {count} accident records")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clear':
            clear_test_data()
        elif sys.argv[1] == 'create':
            populate_test_data()
    else:
        print("Usage:")
        print("  python populate_test_data.py create  - Create test data")
        print("  python populate_test_data.py clear   - Clear test data")
