import os
import smtplib
import requests
import hashlib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

def verify_google_token(token):
    """Verify Google OAuth token and return user info"""
    try:
        response = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={token}')
        if response.status_code == 200:
            user_info = response.json()
            # Verify the token is for our app
            if user_info.get('aud') == os.environ.get('GOOGLE_CLIENT_ID'):
                return {
                    'sub': user_info['sub'],
                    'email': user_info['email'],
                    'name': user_info['name'],
                    'picture': user_info.get('picture', '')
                }
    except Exception as e:
        print(f"Error verifying Google token: {e}")
    return None

def send_verification_email(email, name):
    """Send email verification"""
    try:
        # Create verification token
        token = secrets.token_urlsafe(32)
        
        # Email content
        subject = "Welcome to TypingMaster - Verify Your Email"
        body = f"""
        Hi {name},

        Welcome to TypingMaster! Thank you for signing up.

        Your account has been created successfully. You can now start improving your typing skills with our interactive tests and track your progress over time.

        Features you'll enjoy:
        - Real-time WPM feedback
        - Progress tracking with beautiful charts
        - Streak tracking and badges
        - Leaderboards to compete with others
        - Motivational quotes and TTS support

        Start typing and watch your skills improve!

        Best regards,
        The TypingMaster Team
        """
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('MAIL_USERNAME')
        msg['To'] = email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(os.environ.get('MAIL_USERNAME'), os.environ.get('MAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def generate_share_url(badge_type, achievement):
    """Generate share URLs for social media"""
    base_message = f"🎉 I just earned a new badge on TypingMaster: {achievement}!"
    
    urls = {
        'whatsapp': f"https://wa.me/?text={base_message}",
        'telegram': f"https://t.me/share/url?url=https://typingmaster.app&text={base_message}",
        'twitter': f"https://twitter.com/intent/tweet?text={base_message}&url=https://typingmaster.app",
        'instagram': "https://www.instagram.com/"  # Instagram doesn't support direct text sharing
    }
    
    return urls