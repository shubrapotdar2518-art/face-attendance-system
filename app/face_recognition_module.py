import cv2
import numpy as np
import os
from datetime import datetime, timedelta
from config import Config

class FaceRecognitionSystem:
    def __init__(self):
        self.known_faces = {}
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.load_known_faces()
        
    def load_known_faces(self):
        """Load registered user faces"""
        from app.database import User
        
        try:
            users = User.query.filter_by(is_active=True).all()
            self.known_faces = {}
            
            for user in users:
                if user.photo_path:
                    img_path = os.path.join(Config.FACES_PATH, user.photo_path)
                    if os.path.exists(img_path):
                        # Load and preprocess face image
                        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                        if img is not None:
                            # Detect face in registered image
                            faces = self.face_cascade.detectMultiScale(img, 1.1, 5, minSize=(30, 30))
                            if len(faces) > 0:
                                (x, y, w, h) = faces[0]
                                face_roi = img[y:y+h, x:x+w]
                                face_roi = cv2.resize(face_roi, (100, 100))
                                
                                self.known_faces[user.id] = {
                                    'name': user.name,
                                    'photo_path': img_path,
                                    'face_data': face_roi
                                }
                                print(f"Loaded face for: {user.name}")
            
            print(f"Total loaded: {len(self.known_faces)} face profiles")
        except Exception as e:
            print(f"Error loading faces: {e}")
    
    def register_new_face(self, image_path, user_id, name):
        """Validate face in uploaded image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return False, "Could not read image file"
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return False, "No face detected in the image. Please upload a clear photo of your face."
            
            if len(faces) > 1:
                return False, "Multiple faces detected. Please upload a photo with only one face."
            
            return True, image_path
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def compare_faces(self, face1, face2):
        """Compare two face images"""
        try:
            # Resize both to same size
            face1 = cv2.resize(face1, (100, 100))
            face2 = cv2.resize(face2, (100, 100))
            
            # Calculate histogram similarity
            hist1 = cv2.calcHist([face1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([face2], [0], None, [256], [0, 256])
            
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
            
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Also use template matching
            result = cv2.matchTemplate(face1, face2, cv2.TM_CCOEFF_NORMED)
            template_score = result[0][0]
            
            # Combined score
            final_score = (correlation + template_score) / 2
            
            return max(0, min(1, final_score))  # Clamp between 0 and 1
            
        except Exception as e:
            print(f"Compare error: {e}")
            return 0
    
    def recognize_faces(self, frame):
        """Detect and recognize faces in frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
        )
        
        face_locations = []
        face_names = []
        face_confidences = []
        face_user_ids = []
        
        for (x, y, w, h) in faces:
            # Store location (top, right, bottom, left format)
            face_locations.append((y, x+w, y+h, x))
            
            # Extract and resize face region
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (100, 100))
            
            # Find best match
            best_name = "Unknown"
            best_id = None
            best_score = 0
            
            for user_id, user_data in self.known_faces.items():
                score = self.compare_faces(face_roi, user_data['face_data'])
                print(f"  Comparing with {user_data['name']}: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_name = user_data['name']
                    best_id = user_id
            
            print(f"Best match: {best_name} ({best_score:.3f})")
            
            # Use very low threshold for testing
            if best_score > 0.15 and best_id is not None:
                face_names.append(best_name)
                face_user_ids.append(best_id)
                face_confidences.append(best_score)
            else:
                face_names.append("Unknown")
                face_user_ids.append(None)
                face_confidences.append(best_score)
        
        return face_locations, face_names, face_confidences, face_user_ids
    
    def draw_face_boxes(self, frame, face_locations, face_names, face_confidences):
        """Draw rectangles around detected faces"""
        for (top, right, bottom, left), name, confidence in zip(
            face_locations, face_names, face_confidences
        ):
            # Green for recognized, red for unknown
            if name != "Unknown":
                color = (0, 255, 0)  # Green
            else:
                color = (0, 0, 255)  # Red
            
            # Draw rectangle around face
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            
            # Draw label text
            label = f"{name} ({confidence:.0%})"
            cv2.putText(
                frame, label, (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1
            )
        
        return frame
    
    def capture_attendance(self, user_id):
        """Check if user can mark attendance"""
        from app.database import Attendance
        
        last = Attendance.query.filter_by(user_id=user_id)\
            .order_by(Attendance.timestamp.desc()).first()
        
        if last:
            diff = datetime.utcnow() - last.timestamp
            if diff < Config.ATTENDANCE_COOLDOWN:
                return False, "Attendance already marked recently"
        
        return True, "OK"


class CameraStream:
    def __init__(self):
        self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
        
        if self.camera.isOpened():
            print("✓ Camera opened successfully")
        else:
            print("✗ Failed to open camera")
        
    def get_frame(self):
        success, frame = self.camera.read()
        return frame if success else None
    
    def release(self):
        self.camera.release()
        print("Camera released")

    def recognize_face_from_file(self, file_data):
        """Recognize face from uploaded file (for client-side capture)"""
        try:
            # Convert file data to numpy array
            nparr = np.frombuffer(file_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return None, None, 0, "Could not decode image"
            
            # Use existing recognize_faces logic
            face_locations, face_names, face_confidences, face_user_ids = \
                self.recognize_faces(img)
            
            return face_locations, face_names, face_confidences, face_user_ids
        except Exception as e:
            print(f"Error recognizing face from file: {e}")
            return None, None, 0, str(e)