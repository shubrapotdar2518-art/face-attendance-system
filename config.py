import os
from datetime import timedelta

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'data/database/attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    FACE_ENCODINGS_PATH = os.path.join(BASE_DIR, 'data/encodings')
    FACES_PATH = os.path.join(BASE_DIR, 'data/faces')
    MODELS_PATH = os.path.join(BASE_DIR, 'models')
    
    ATTENDANCE_THRESHOLD = 0.6
    MIN_FACE_SIZE = (30, 30)
    ATTENDANCE_COOLDOWN = timedelta(hours=1)
    
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data/faces')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    os.makedirs(FACE_ENCODINGS_PATH, exist_ok=True)
    os.makedirs(FACES_PATH, exist_ok=True)
    os.makedirs(MODELS_PATH, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, 'data/database'), exist_ok=True)