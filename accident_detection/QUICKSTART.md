# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate  # Windows: use this
# source venv/bin/activate  # macOS/Linux: use this

pip install -r requirements.txt
```

### 2. Setup Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Run Server
```bash
python manage.py runserver
```

### 4. Access Application
- Dashboard: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin

---

## Next Steps

1. **Upload a Video**:
   - Go to http://127.0.0.1:8000/upload/
   - Choose a traffic/CCTV video file
   - Enter location and video ID
   - Click "Upload & Start Processing"

2. **View Results**:
   - Check dashboard for detected accidents
   - Click on accident to see details
   - View statistics for system overview

---

## Useful Commands

```bash
# Create superuser if you forgot password
python manage.py createsuperuser

# Clear old data
python manage.py shell
# Then in shell:
# from detection.models import Accident
# Accident.objects.all().delete()
# exit()

# Check database status
python manage.py dbshell

# View logs
tail -f accident_detection.log
```

---

## For Development

### Run with Auto-reload
```bash
python manage.py runserver 0.0.0.0:8000
```

### Django Shell
```bash
python manage.py shell

# Test YOLO
from video_processor.yolo_detector import YOLODetector
detector = YOLODetector()
detector.load_model()

# Query accidents
from detection.models import Accident
accidents = Accident.objects.all()
for acc in accidents:
    print(f"{acc.id}: {acc.location} - {acc.confidence_score}%")
```

---

## Troubleshooting

**Module not found error?**
```bash
pip install -r requirements.txt
```

**Database error?**
```bash
rm db.sqlite3
python manage.py migrate
```

**YOLO not loading?**
```bash
pip install --upgrade torch torchvision
python -c "import torch; torch.hub.load('ultralytics/yolov5', 'yolov5s')"
```

---

**Happy coding! 🚀**
