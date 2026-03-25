# 🚀 STEP-BY-STEP INSTALLATION GUIDE

## Complete Setup Instructions for Windows/macOS/Linux

---

## ⚡ QUICK START (5 minutes)

### For Windows Users:

```batch
REM 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

REM 2. Install dependencies
pip install -r requirements.txt

REM 3. Initialize database
python manage.py migrate
python manage.py createsuperuser

REM 4. Run server
python manage.py runserver
```

**Open browser**: http://127.0.0.1:8000

---

### For macOS/Linux Users:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python manage.py migrate
python manage.py createsuperuser

# 4. Run server
python manage.py runserver
```

**Open browser**: http://127.0.0.1:8000

---

## 📋 DETAILED INSTALLATION

### Prerequisites

✅ **Python 3.8+**
```bash
python --version  # Should show 3.8 or higher
```

✅ **pip (Python package manager)**
```bash
pip --version
```

✅ **Git** (optional, for version control)
```bash
git --version
```

---

### Step 1: Extract/Setup Project

```bash
# Navigate to project directory
cd accident_detection

# Verify files exist
ls -la  # macOS/Linux
dir     # Windows
```

**Expected files**:
- `manage.py` ✅
- `requirements.txt` ✅
- `README.md` ✅
- `accident_detection/` folder ✅
- `detection/` folder ✅
- `video_processor/` folder ✅

---

### Step 2: Create Virtual Environment

**Why**: Isolates project dependencies from system Python.

#### Windows:
```batch
python -m venv venv
venv\Scripts\activate

REM Your prompt should show (venv) at the start
```

#### macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate

# Your prompt should show (venv) at the start
```

**Verify activation**:
```bash
which python  # Should point to venv folder
```

---

### Step 3: Upgrade pip

Ensures you have the latest package installer:

```bash
python -m pip install --upgrade pip setuptools wheel
```

---

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed**:
- Django 4.2.8 - Web framework
- OpenCV 4.8 - Video processing
- PyTorch 2.1 - Deep learning
- YOLOv5 - Object detection
- Pillow - Image processing
- NumPy - Numerical computing

**Installation time**: 5-10 minutes (first time, including YOLO model)

**⚠️ If installation fails**:
```bash
# Check Python version
python --version

# Try alternative command
pip3 install -r requirements.txt

# Or verbose mode
pip install -r requirements.txt -v
```

---

### Step 5: Initialize Database

#### Create Migrations:
```bash
python manage.py migrate
```

**This**:
- Creates `db.sqlite3` database file
- Sets up accident and video session tables
- Prepares system tables

#### Create Admin Account:
```bash
python manage.py createsuperuser
```

**Follow prompts**:
```
Username: admin
Email: admin@example.com
Password: (enter strong password)
Password (again): (confirm)
Superuser created successfully.
```

**Save these credentials** - you'll need them for admin panel!

---

### Step 6: Collect Static Files

Prepares CSS, JavaScript, and image files:

```bash
python manage.py collectstatic --noinput
```

---

### Step 7: Run Development Server

```bash
python manage.py runserver
```

**Expected output**:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK (or CONTROL-C on Mac/Linux).
```

✅ **Server is running!**

---

## 🌐 Accessing the Application

### Main Pages:

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/ | Dashboard home |
| http://127.0.0.1:8000/upload/ | Upload video |
| http://127.0.0.1:8000/accidents/ | View accidents |
| http://127.0.0.1:8000/statistics/ | System stats |
| http://127.0.0.1:8000/about/ | About project |
| http://127.0.0.1:8000/admin/ | Admin panel |

### First Login:

1. Go to http://127.0.0.1:8000/admin/
2. Enter username and password created earlier
3. View database in admin panel

---

## 🎬 Using the Application

### Step 1: Upload Video

1. Go to http://127.0.0.1:8000/upload/
2. Click "Choose File" and select a video:
   - Format: MP4, AVI, MOV (recommended: MP4)
   - Size: Any size (tested up to 500MB)
   - Content: Traffic/CCTV footage

3. Enter Location: e.g., "Highway 101, Exit 5"
4. Enter Video ID: e.g., "camera_01"
5. Click "Upload & Start Processing"

**Example video sources**:
- YouTube traffic camera feeds (download with youtube-dl)
- Your own dashcam footage
- Simulated videos from traffic simulation software

### Step 2: Monitor Processing

1. Video is automatically analyzed
2. Check dashboard for updates
3. Results appear within minutes

**Processing time depends on**:
- Video length (typically 5-10 min per hour)
- Video resolution
- System resources
- Number of frames with vehicles

### Step 3: View Results

1. Go to http://127.0.0.1:8000/accidents/
2. See all detected accidents
3. Filter by location, date, confidence
4. Click "View" for detailed information

### Step 4: View Statistics

1. Go to http://127.0.0.1:8000/statistics/
2. See system overview
3. Accidents by location
4. Detection performance metrics

---

## 🛠️ Troubleshooting

### Issue: "Module not found" Error

```
ModuleNotFoundError: No module named 'django'
```

**Solution**:
```bash
# Check virtual environment is activated
# Windows: You should see (venv) in prompt
# macOS/Linux: You should see (venv) in prompt

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

### Issue: "Port Already in Use" Error

```
Error: That port is already in use.
```

**Solution - Option 1** (Change port):
```bash
python manage.py runserver 8001
# Then access: http://127.0.0.1:8001
```

**Solution - Option 2** (Kill process):
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID [PID] /F

# macOS/Linux
lsof -i :8000
kill -9 [PID]
```

---

### Issue: Database Error

```
sqlite3.OperationalError: no such table
```

**Solution**:
```bash
# Reset database
rm db.sqlite3  # macOS/Linux
del db.sqlite3  # Windows

# Reapply migrations
python manage.py migrate
python manage.py createsuperuser
```

---

### Issue: YOLO Model Not Loading

```
Error: Failed to load YOLO model
```

**Solution**:
```bash
# Download model manually
python -c "import torch; torch.hub.load('ultralytics/yolov5', 'yolov5s')"

# Verify PyTorch
python -c "import torch; print(torch.__version__)"

# Upgrade packages
pip install --upgrade torch torchvision ultralytics
```

---

### Issue: Out of Memory

```
RuntimeError: CUDA out of memory
MemoryError: Unable to allocate memory
```

**Solution**:
1. Close other applications
2. Reduce video resolution
3. Process smaller videos first
4. Add more RAM or use cloud instance

---

### Issue: Static Files Not Loading

CSS and JavaScript not working (site looks broken):

**Solution**:
```bash
python manage.py collectstatic --noinput
# Restart server
python manage.py runserver
```

---

### Issue: Admin Panel Inaccessible

**Solution**:
```bash
# Recreate admin user
python manage.py createsuperuser

# Or reset password
python manage.py shell
# Then in shell:
from django.contrib.auth.models import User
u = User.objects.get(username='admin')
u.set_password('newpassword')
u.save()
exit()
```

---

## 🧪 Testing the Installation

### Test 1: Verify Django

```bash
python -c "import django; print(django.get_version())"
# Should print: 4.2.8
```

### Test 2: Verify OpenCV

```bash
python -c "import cv2; print(cv2.__version__)"
# Should print: 4.8.1.78
```

### Test 3: Verify PyTorch

```bash
python -c "import torch; print(torch.__version__)"
# Should print: 2.1.1
```

### Test 4: Verify YOLO

```bash
python -c "import torch; model = torch.hub.load('ultralytics/yolov5', 'yolov5s'); print('YOLO loaded')"
# Should print: YOLO loaded
```

### Test 5: Create Test Data (Optional)

```bash
python manage.py shell
from detection.models import Accident
from django.utils import timezone

acc = Accident.objects.create(
    location="Test Location",
    video_id="test_video",
    confidence_score=85,
    vehicle_count=2,
    description="Test accident"
)

print(f"Created: {acc}")
exit()
```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (pip install -r requirements.txt)
- [ ] Database migrations applied (python manage.py migrate)
- [ ] Superuser created
- [ ] Server runs without errors (python manage.py runserver)
- [ ] Dashboard accessible (http://127.0.0.1:8000/)
- [ ] Admin panel accessible (http://127.0.0.1:8000/admin/)
- [ ] Video upload page works
- [ ] YOLO model loads successfully

---

## 🎯 Next Steps After Installation

1. **Create test data**: `python populate_test_data.py create`
2. **Upload a test video** from /upload/ page
3. **Monitor results** on dashboard
4. **Explore admin panel** at /admin/
5. **Read README.md** for detailed documentation

---

## 📞 Common Commands Reference

```bash
# Start server
python manage.py runserver

# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Django shell
python manage.py shell

# Reset database
python manage.py migrate zero detection
python manage.py migrate

# View logs
tail -f accident_detection.log  # macOS/Linux
type accident_detection.log     # Windows (continuous)

# Deactivate virtual environment
deactivate
```

---

## 🚀 You're Ready!

Your accident detection system is now ready to use.

**Next**: Upload a video to test the system!

---

**Need help?** Check README.md or QUICKSTART.md for more information.

**Happy accident detection! 🎉**
