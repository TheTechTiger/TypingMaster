import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
import hashlib
from database import init_db, get_user_by_email, create_user, save_typing_result, get_user_stats, get_leaderboard, get_user_by_id, update_user_streak, get_all_users, create_badge
from auth import verify_google_token, send_verification_email
import edge_tts
import asyncio
import base64

if os.name == 'nt':
    with open(".env", "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# Initialize database
init_db()

# Motivational quotes
MOTIVATIONAL_QUOTES = [
    "The expert in anything was once a beginner.",
    "Practice makes progress, not perfection.",
    "Every keystroke brings you closer to mastery.",
    "Speed comes with accuracy, accuracy comes with practice.",
    "Your fingers are your instruments of success.",
    "Consistency is the key to improvement.",
    "Great typists are made, not born.",
    "Focus on accuracy first, speed will follow.",
    "Every mistake is a lesson learned.",
    "Progress, not perfection, is the goal."
]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Check if user already exists
    if get_user_by_email(email):
        return jsonify({'success': False, 'message': 'User already exists'})
    
    # Create user
    user_id = create_user(name, email, password)
    if user_id:
        # Send verification email
        send_verification_email(email, name)
        return jsonify({'success': True, 'message': 'Account created successfully. Please check your email for verification.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to create account'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = get_user_by_email(email)
    if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    token = data.get('token')
    
    user_info = verify_google_token(token)
    if user_info:
        user = get_user_by_email(user_info['email'])
        if not user:
            # Create new user
            user_id = create_user(user_info['name'], user_info['email'], '', google_id=user_info['sub'])
        else:
            user_id = user['id']
        
        session['user_id'] = user_id
        session['user_name'] = user_info['name']
        session['user_email'] = user_info['email']
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid Google token'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_stats = get_user_stats(session['user_id'])
    all_users = get_all_users()
    return render_template('dashboard.html', stats=user_stats, all_users=all_users, current_user_id=session['user_id'])

@app.route('/test')
@login_required
def test():
    return render_template('test.html')

@app.route('/leaderboard')
@login_required
def leaderboard():
    leaders = get_leaderboard()
    return render_template('leaderboard.html', leaders=leaders)

@app.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return redirect(url_for('dashboard'))
    
    user_stats = get_user_stats(user_id)
    is_own_profile = (user_id == session['user_id'])
    
    return render_template('dashboard.html', 
                         stats=user_stats, 
                         user=user, 
                         is_own_profile=is_own_profile,
                         current_user_id=session['user_id'])

@app.route('/submit-result', methods=['POST'])
@login_required
def submit_result():
    data = request.get_json()
    wpm = data.get('wpm')
    accuracy = data.get('accuracy')
    test_duration = data.get('duration', 60)
    
    if wpm is None or accuracy is None:
        return jsonify({'success': False, 'message': 'Invalid data'})
    
    # Save result
    save_typing_result(session['user_id'], wpm, accuracy, test_duration)
    
    # Update streak
    update_user_streak(session['user_id'])
    
    # Check for milestones and create badges
    user_stats = get_user_stats(session['user_id'])
    badges_earned = []
    
    # Check for streak milestones
    current_streak = user_stats['current_streak']
    if current_streak in [5, 10, 15, 30, 50, 100]:
        badge_path = create_badge(session['user_id'], f"{current_streak} Day Streak", f"Maintained {current_streak} day typing streak!")
        badges_earned.append({'type': 'streak', 'days': current_streak, 'image': badge_path})
    
    # Check for WPM records
    best_wpm = user_stats['best_wpm']
    if wpm == best_wpm and wpm >= 40:  # New personal record
        milestone = None
        if wpm >= 100:
            milestone = "Lightning Fingers"
        elif wpm >= 80:
            milestone = "Speed Demon"
        elif wpm >= 60:
            milestone = "Fast Typer"
        elif wpm >= 40:
            milestone = "Speed Boost"
        
        if milestone:
            badge_path = create_badge(session['user_id'], milestone, f"Achieved {wpm} WPM!")
            badges_earned.append({'type': 'wpm', 'wpm': wpm, 'title': milestone, 'image': badge_path})
    
    # Get a random motivational quote
    import random
    quote = random.choice(MOTIVATIONAL_QUOTES)
    
    return jsonify({
        'success': True, 
        'badges': badges_earned,
        'quote': quote,
        'current_streak': current_streak
    })

@app.route('/generate-speech', methods=['POST'])
@login_required
def generate_speech():
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({'success': False, 'message': 'No text provided'})
    
    async def create_speech():
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_data = loop.run_until_complete(create_speech())
        loop.close()
        
        # Convert to base64 for JSON response
        audio_b64 = base64.b64encode(audio_data).decode()
        return jsonify({'success': True, 'audio': audio_b64})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/typing-text')
def typing_text():
    texts = [
        "The quick brown fox jumps over the lazy dog. This sentence contains all letters of the alphabet and is perfect for typing practice.",
        "In the digital age, typing skills have become essential for productivity and communication in both personal and professional contexts.",
        "Practice makes perfect, and consistent daily typing exercises can significantly improve your speed and accuracy over time.",
        "Technology continues to evolve rapidly, changing the way we work, communicate, and interact with the world around us.",
        "The art of typing efficiently requires muscle memory, proper finger placement, and regular practice to achieve mastery."
    ]
    
    import random
    return jsonify({'text': random.choice(texts)})

@app.route('/favicon.ico')
def favicon():
    return send_file('favico.png', mimetype='image/png')

@app.route('/get-typing-stats')
@login_required
def get_typing_stats():
    stats = get_user_stats(session['user_id'])
    return jsonify(stats)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)