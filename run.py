import os
from app.main import app, db, socketio

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created!")
    
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)