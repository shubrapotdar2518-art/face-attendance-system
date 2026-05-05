from app.main import app, db, socketio
import eventlet

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")
    
    print("=" * 50)
    print("Face Recognition Attendance System")
    print("=" * 50)
    print("Server running on: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    
    # Use eventlet for WebSocket support
    eventlet.monkey_patch()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)