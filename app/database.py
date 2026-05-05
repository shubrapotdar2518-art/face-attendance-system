from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    face_encoding = db.Column(db.Text)
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    attendance_records = db.relationship('Attendance', backref='user', lazy=True)
    
    def set_face_encoding(self, encoding):
        """Convert encoding to JSON string - handles multiple types"""
        if encoding is None:
            self.face_encoding = None
        elif isinstance(encoding, str):
            # Already a string, just store it
            self.face_encoding = encoding
        elif hasattr(encoding, 'tolist'):
            # NumPy array - convert to list then JSON
            self.face_encoding = json.dumps(encoding.tolist())
        else:
            # Other types - try to convert directly
            try:
                self.face_encoding = json.dumps(encoding)
            except:
                self.face_encoding = str(encoding)
    
    def get_face_encoding(self):
        """Convert JSON string back to data"""
        if self.face_encoding:
            try:
                return json.loads(self.face_encoding)
            except:
                return self.face_encoding
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'position': self.position,
            'photo_path': self.photo_path,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    photo_path = db.Column(db.String(255))
    location = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Unknown',
            'employee_id': self.user.employee_id if self.user else 'Unknown',
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'confidence': self.confidence,
            'photo_path': self.photo_path,
            'location': self.location
        }


class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_query = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_query': self.user_query,
            'bot_response': self.bot_response,
            'timestamp': self.timestamp.isoformat()
        }