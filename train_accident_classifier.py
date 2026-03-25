import os
import random
import glob
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import models, transforms
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


# --- CONFIGURATION ----------------------------------------------------------------
VIDEO_ROOT = Path('media/uploads')
ACCIDENT_DIR = VIDEO_ROOT / 'Accident'
NOACCIDENT_DIR = VIDEO_ROOT / 'NoAccident'
MODEL_SAVE_PATH = Path('models') / 'accident_classifier.pth'
BATCH_SIZE = 16
IMG_SIZE = 224
EPOCHS = 10
LR = 1e-4
SAMPLE_EVERY_N_FRAMES = 5
SEED = 42
NUM_WORKERS = 4 if os.name != 'nt' else 0
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Create model output folder
MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)


# --- DATA PREPROCESSING -----------------------------------------------------------

def extract_sampled_frames(video_path, frame_skip=SAMPLE_EVERY_N_FRAMES, max_frames=300):
    """Sample frames from a video (every Nth frame) and return them as BGR numpy arrays."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f'Cannot open video: {video_path}')

    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % frame_skip == 0:
            frames.append(frame)
            if len(frames) >= max_frames:
                break
        idx += 1
    cap.release()

    # remove potential duplicates by hashing frame data
    unique_frames = []
    seen = set()
    for f in frames:
        h = hash(f.tobytes())
        if h not in seen:
            seen.add(h)
            unique_frames.append(f)
    return unique_frames


# --- DATASET ----------------------------------------------------------------------

class VideoFrameDataset(Dataset):
    """Dataset for frame-based accident/no-accident classification."""

    def __init__(self, video_paths, labels, transform=None, frame_skip=SAMPLE_EVERY_N_FRAMES):
        self.samples = []  # list of tuples (frame_numpy, label)
        self.transform = transform

        random.seed(SEED)
        zipped = list(zip(video_paths, labels))
        random.shuffle(zipped)

        for video_path, label in zipped:
            frames = extract_sampled_frames(video_path, frame_skip=frame_skip)
            for frame in frames:
                self.samples.append((frame, label))

        if len(self.samples) == 0:
            raise RuntimeError('No frames in dataset. Check the media/uploads dataset folders.')

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        frame, label = self.samples[idx]

        # Convert BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)

        if self.transform is not None:
            frame = self.transform(frame)
        else:
            frame = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0

        return frame, torch.tensor(label, dtype=torch.long)


# --- MODEL ------------------------------------------------------------------------

def build_model(num_classes=2):
    model = models.resnet18(pretrained=True)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def get_transforms():
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


# --- TRAINING + EVAL -------------------------------------------------------------


def train_loop(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    for images, labels in loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)

        proba = torch.softmax(outputs, dim=1)
        preds = torch.argmax(proba, dim=1)
        all_preds.extend(preds.detach().cpu().numpy())
        all_labels.extend(labels.detach().cpu().numpy())

    epoch_loss = total_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    return epoch_loss, epoch_acc


def eval_loop(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * images.size(0)

            proba = torch.softmax(outputs, dim=1)
            preds = torch.argmax(proba, dim=1)
            all_preds.extend(preds.detach().cpu().numpy())
            all_labels.extend(labels.detach().cpu().numpy())

    epoch_loss = total_loss / len(loader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)
    p = precision_score(all_labels, all_preds, zero_division=0)
    r = recall_score(all_labels, all_preds, zero_division=0)
    f1 = f1_score(all_labels, all_preds, zero_division=0)
    return epoch_loss, epoch_acc, p, r, f1


# --- VIDEO-LEVEL INFERENCE --------------------------------------------------------

def predict_video(model, video_path, transform, threshold=0.5, frame_skip=SAMPLE_EVERY_N_FRAMES):
    model.eval()
    frames = extract_sampled_frames(video_path, frame_skip=frame_skip)
    if not frames:
        raise RuntimeError(f'No frames in video: {video_path}')

    preds = []
    with torch.no_grad():
        for frame in frames:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
            frame_tensor = transform(frame_resized).unsqueeze(0).to(DEVICE)
            out = model(frame_tensor)
            prob = torch.softmax(out, dim=1)[0, 1].item()  # accident probability
            preds.append(prob)

    # majority voting on threshold
    accident_votes = sum(1 for p in preds if p >= threshold)
    noaccident_votes = len(preds) - accident_votes
    label = 1 if accident_votes > noaccident_votes else 0
    return label, accident_votes, noaccident_votes, preds


# --- METRICS ----------------------------------------------------------------------


def compute_metrics(y_true, y_pred):
    tp = sum((t == 1 and p == 1) for t, p in zip(y_true, y_pred))
    tn = sum((t == 0 and p == 0) for t, p in zip(y_true, y_pred))
    fp = sum((t == 0 and p == 1) for t, p in zip(y_true, y_pred))
    fn = sum((t == 1 and p == 0) for t, p in zip(y_true, y_pred))

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }


# --- DATASET LOADING -------------------------------------------------------------

def collect_video_paths(root_dir):
    accident_paths = sorted(glob.glob(str(Path(root_dir) / 'Accident' / '*.mp4')))
    noaccident_paths = sorted(glob.glob(str(Path(root_dir) / 'NoAccident' / '*.mp4')))

    paths = accident_paths + noaccident_paths
    labels = [1] * len(accident_paths) + [0] * len(noaccident_paths)
    return paths, labels


def prepare_data_loaders(batch_size=BATCH_SIZE, val_ratio=0.2):
    paths, labels = collect_video_paths(VIDEO_ROOT)
    if len(paths) == 0:
        raise RuntimeError('No video files found. Ensure dataset is under media/uploads/Accident and media/uploads/NoAccident.')

    # Build dataset from frame samples
    ds = VideoFrameDataset(paths, labels, transform=get_transforms())
    val_size = int(len(ds) * val_ratio)
    train_size = len(ds) - val_size

    train_ds, val_ds = random_split(ds, [train_size, val_size], generator=torch.Generator().manual_seed(SEED))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=NUM_WORKERS)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=NUM_WORKERS)
    return train_loader, val_loader


# --- MAIN SCRIPT -----------------------------------------------------------------

def run_training():
    torch.manual_seed(SEED)
    train_loader, val_loader = prepare_data_loaders()

    model = build_model(num_classes=2)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)

    best_val_f1 = 0.0

    for epoch in range(1, EPOCHS + 1):
        train_loss, train_acc = train_loop(model, train_loader, criterion, optimizer, DEVICE)
        val_loss, val_acc, val_precision, val_recall, val_f1 = eval_loop(model, val_loader, criterion, DEVICE)

        print(f'[Epoch {epoch}/{EPOCHS}]',
              f'Train Loss: {train_loss:.4f}', f'Train Acc: {train_acc:.4f}',
              f'Val Loss: {val_loss:.4f}', f'Val Acc: {val_acc:.4f}',
              f'Val P: {val_precision:.4f}', f'Val R: {val_recall:.4f}', f'Val F1: {val_f1:.4f}')

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f'Best model saved to {MODEL_SAVE_PATH} (F1: {best_val_f1:.4f})')

        scheduler.step()

    print('Training complete.')


# --- UTILITY ---------------------------------------------------------------------

def predict_dataset(model, video_paths, labels, transform):
    model.eval()
    y_pred = []
    y_true = []

    for video_path, label in zip(video_paths, labels):
        pred_label, _, _, _ = predict_video(model, video_path, transform)
        y_pred.append(pred_label)
        y_true.append(label)

    return compute_metrics(y_true, y_pred)


if __name__ == '__main__':
    run_training()
