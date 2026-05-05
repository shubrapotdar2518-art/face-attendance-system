from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()
import cv2
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import base64

from config import Config
from app.database import db, User, Attendance, ChatMessage
from app.face_recognition_module import FaceRecognitionSystem, CameraStream
from app.chatbot import AttendanceChatbot

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config.from_object(Config)

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)

face_system = None
camera_stream = None
chatbot = AttendanceChatbot()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    total_users = User.query.filter_by(is_active=True).count()
    total_attendance = Attendance.query.count()
    
    today = datetime.utcnow().date()
    today_attendance = Attendance.query.filter(
        db.func.date(Attendance.timestamp) == today
    ).count()
    
    recent_attendance = Attendance.query.order_by(
        Attendance.timestamp.desc()
    ).limit(10).all()
    
    return render_template('dashboard.html',
                         total_users=total_users,
                         total_attendance=total_attendance,
                         today_attendance=today_attendance,
                         recent_attendance=recent_attendance)

@app.route('/register', methods=['GET', 'POST'])
def register():
    global face_system
    
    if request.method == 'POST':
        try:
            employee_id = request.form.get('employee_id')
            name = request.form.get('name')
            email = request.form.get('email')
            department = request.form.get('department')
            position = request.form.get('position')
            
            existing_user = User.query.filter_by(employee_id=employee_id).first()
            if existing_user:
                return jsonify({'success': False, 'message': 'Employee ID already exists'})
            
            if 'photo' not in request.files:
                return jsonify({'success': False, 'message': 'No photo uploaded'})
            
            file = request.files['photo']
            
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No photo selected'})
            
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{employee_id}_{uuid.uuid4().hex}.jpg")
                filepath = os.path.join(Config.FACES_PATH, filename)
                file.save(filepath)
                
                user = User(
                    employee_id=employee_id,
                    name=name,
                    email=email,
                    department=department,
                    position=position,
                    photo_path=filename
                )
                
                if face_system is None:
                    face_system = FaceRecognitionSystem()
                
                success, result = face_system.register_new_face(filepath, user.id, name)
                
                if success:
                    user.set_face_encoding(result)
                    db.session.add(user)
                    db.session.commit()
                    
                    face_system.load_known_faces()
                    
                    return jsonify({'success': True, 'message': 'User registered successfully'})
                else:
                    os.remove(filepath)
                    return jsonify({'success': False, 'message': result})
            
            return jsonify({'success': False, 'message': 'Invalid file type'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    return render_template('register.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/reports')
def reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id')
    
    query = Attendance.query
    
    if start_date:
        query = query.filter(Attendance.timestamp >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Attendance.timestamp <= datetime.fromisoformat(end_date))
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    attendance_records = query.order_by(Attendance.timestamp.desc()).all()
    users = User.query.filter_by(is_active=True).all()
    
    return render_template('reports.html', 
                         attendance_records=attendance_records,
                         users=users)

@app.route('/api/users')
def get_users():
    users = User.query.filter_by(is_active=True).all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/attendance/today')
def get_today_attendance():
    today = datetime.utcnow().date()
    attendance_records = Attendance.query.filter(
        db.func.date(Attendance.timestamp) == today
    ).all()
    return jsonify([record.to_dict() for record in attendance_records])

@app.route('/api/mark_attendance', methods=['POST'])
def mark_attendance():
    global face_system
    
    try:
        data = request.json
        user_id = data.get('user_id')
        confidence = data.get('confidence')
        
        if face_system is None:
            face_system = FaceRecognitionSystem()
        
        can_mark, message = face_system.capture_attendance(user_id)
        
        if not can_mark:
            return jsonify({'success': False, 'message': message})
        
        current_hour = datetime.utcnow().hour
        if current_hour < 9:
            status = 'early'
        elif current_hour <= 10:
            status = 'present'
        else:
            status = 'late'
        
        attendance = Attendance(
            user_id=user_id,
            status=status,
            confidence=confidence,
            location='Main Office'
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        user = User.query.get(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {user.name}',
            'data': attendance.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('start_camera')
def handle_start_camera():
    global camera_stream, face_system
    
    try:
        if camera_stream is None:
            camera_stream = CameraStream()
        
        if face_system is None:
            face_system = FaceRecognitionSystem()
        
        emit('camera_started', {'success': True})
    except Exception as e:
        emit('camera_started', {'success': False, 'error': str(e)})

@socketio.on('stop_camera')
def handle_stop_camera():
    global camera_stream
    
    if camera_stream:
        camera_stream.release()
        camera_stream = None
    
    emit('camera_stopped', {'success': True})

@socketio.on('process_frame')
def handle_process_frame(data):
    global camera_stream, face_system
    
    if camera_stream is None:
        return
    
    if face_system is None:
        face_system = FaceRecognitionSystem()
    
    frame = camera_stream.get_frame()
    
    if frame is None:
        return
    
    try:
        face_locations, face_names, face_confidences, face_user_ids = \
            face_system.recognize_faces(frame)
        
        frame = face_system.draw_face_boxes(
            frame, face_locations, face_names, face_confidences
        )
        
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        detected_faces = []
        for name, confidence, user_id in zip(face_names, face_confidences, face_user_ids):
            if name != "Unknown":
                detected_faces.append({
                    'name': name,
                    'confidence': confidence,
                    'user_id': user_id
                })
        
        emit('frame_processed', {
            'frame': frame_base64,
            'faces': detected_faces
        })
    except Exception as e:
        print(f"Error processing frame: {e}")

@socketio.on('chat_message')
def handle_chat_message(data):
    message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    try:
        response = chatbot.get_response(message, session_id)
        
        chat_record = ChatMessage(
            user_query=message,
            bot_response=response,
            session_id=session_id
        )
        db.session.add(chat_record)
        db.session.commit()
        
        emit('chat_response', {
            'message': response,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        emit('chat_response', {
            'message': f'Sorry, I encountered an error: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        })

# Initialize database tables
@app.before_request
def create_tables():
    if not hasattr(app, 'tables_created'):
        db.create_all()
        app.tables_created = True

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)