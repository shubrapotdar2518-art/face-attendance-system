import random
from datetime import datetime, timedelta
from app.database import User, Attendance, db

class AttendanceChatbot:
    def __init__(self):
        self.context = {}
        self.intents = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
            'attendance_check': ['attendance', 'present', 'absent', 'check attendance'],
            'user_info': ['who is', 'tell me about', 'information about', 'details of'],
            'statistics': ['stats', 'statistics', 'report', 'summary'],
            'help': ['help', 'what can you do', 'commands', 'how to use'],
            'goodbye': ['bye', 'goodbye', 'see you', 'exit']
        }
        
        self.responses = {
            'greeting': [
                "Hello! How can I help you with attendance today?",
                "Hi there! I'm your attendance assistant. What would you like to know?",
                "Good day! How may I assist you?"
            ],
            'help': [
                """I can help you with:
                - Check attendance records (e.g., "show today's attendance")
                - Get user information (e.g., "who is John Doe?")
                - View statistics (e.g., "show attendance stats")
                - Answer general queries about the system
                
                Just ask me anything!"""
            ],
            'goodbye': [
                "Goodbye! Have a great day!",
                "See you later! Feel free to come back anytime.",
                "Bye! Take care!"
            ]
        }
    
    def detect_intent(self, message):
        message_lower = message.lower()
        
        for intent, keywords in self.intents.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'unknown'
    
    def get_response(self, message, session_id=None):
        intent = self.detect_intent(message)
        
        if intent == 'greeting':
            return random.choice(self.responses['greeting'])
        
        elif intent == 'help':
            return self.responses['help'][0]
        
        elif intent == 'goodbye':
            return random.choice(self.responses['goodbye'])
        
        elif intent == 'attendance_check':
            return self.get_attendance_info(message)
        
        elif intent == 'user_info':
            return self.get_user_info(message)
        
        elif intent == 'statistics':
            return self.get_statistics(message)
        
        else:
            return self.handle_specific_query(message)
    
    def get_attendance_info(self, message):
        message_lower = message.lower()
        
        if 'today' in message_lower:
            today = datetime.utcnow().date()
            attendance_records = Attendance.query.filter(
                db.func.date(Attendance.timestamp) == today
            ).all()
            
            if not attendance_records:
                return "No attendance records found for today."
            
            response = f"📊 Today's Attendance ({len(attendance_records)} records):\n\n"
            for record in attendance_records[:10]:
                response += f"✓ {record.user.name} - {record.timestamp.strftime('%I:%M %p')} - {record.status}\n"
            
            if len(attendance_records) > 10:
                response += f"\n... and {len(attendance_records) - 10} more"
            
            return response
        
        elif 'week' in message_lower:
            week_ago = datetime.utcnow() - timedelta(days=7)
            count = Attendance.query.filter(
                Attendance.timestamp >= week_ago
            ).count()
            
            return f"📈 This week's attendance: {count} total check-ins"
        
        elif 'month' in message_lower:
            month_ago = datetime.utcnow() - timedelta(days=30)
            count = Attendance.query.filter(
                Attendance.timestamp >= month_ago
            ).count()
            
            return f"📈 This month's attendance: {count} total check-ins"
        
        return "Please specify: today's attendance, this week's attendance, or this month's attendance"
    
    def get_user_info(self, message):
        users = User.query.filter_by(is_active=True).all()
        
        for user in users:
            if user.name.lower() in message.lower():
                attendance_count = Attendance.query.filter_by(user_id=user.id).count()
                
                response = f"""
👤 User Information:
Name: {user.name}
Employee ID: {user.employee_id}
Email: {user.email}
Department: {user.department}
Position: {user.position}
Total Attendance: {attendance_count} times
Registered: {user.created_at.strftime('%B %d, %Y')}
                """
                return response.strip()
        
        return "User not found. Please provide a valid name."
    
    def get_statistics(self, message):
        total_users = User.query.filter_by(is_active=True).count()
        total_attendance = Attendance.query.count()
        
        today = datetime.utcnow().date()
        today_attendance = Attendance.query.filter(
            db.func.date(Attendance.timestamp) == today
        ).count()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        week_attendance = Attendance.query.filter(
            Attendance.timestamp >= week_ago
        ).count()
        
        response = f"""
📊 System Statistics:

👥 Total Registered Users: {total_users}
📝 Total Attendance Records: {total_attendance}
📅 Today's Check-ins: {today_attendance}
📈 This Week's Check-ins: {week_attendance}
        """
        
        return response.strip()
    
    def handle_specific_query(self, message):
        message_lower = message.lower()
        
        if 'how many' in message_lower:
            if 'user' in message_lower or 'employee' in message_lower:
                count = User.query.filter_by(is_active=True).count()
                return f"There are currently {count} registered users in the system."
            
            elif 'attendance' in message_lower:
                count = Attendance.query.count()
                return f"There are {count} total attendance records in the system."
        
        if 'last' in message_lower and 'attendance' in message_lower:
            last_record = Attendance.query.order_by(Attendance.timestamp.desc()).first()
            if last_record:
                return f"Last attendance: {last_record.user.name} at {last_record.timestamp.strftime('%I:%M %p on %B %d, %Y')}"
            return "No attendance records found."
        
        return """I'm not sure I understand. Try asking me:
        - "Show today's attendance"
        - "Who is [name]?"
        - "Show statistics"
        - "How many users are registered?"
        
        Or type 'help' for more options."""