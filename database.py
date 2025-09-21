import sqlite3
import os
import hashlib
from datetime import datetime, date
from PIL import Image, ImageDraw, ImageFont
import anybadge

# Determine database path based on OS
if os.name == 'nt':  # Windows
    DB_PATH = 'web.db'
else:  # POSIX (Linux, macOS, Vercel)
    DB_PATH = '/tmp/web.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            google_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_test_date DATE,
            total_tests INTEGER DEFAULT 0,
            verified BOOLEAN DEFAULT 0
        )
    ''')
    
    # Typing results table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS typing_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            wpm REAL NOT NULL,
            accuracy REAL NOT NULL,
            test_duration INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Badges table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            image_path TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(name, email, password, google_id=None):
    """Create a new user"""
    conn = get_db_connection()
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest() if password else None
        cursor = conn.execute(
            'INSERT INTO users (name, email, password, google_id) VALUES (?, ?, ?, ?)',
            (name, email, hashed_password, google_id)
        )
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    """Get user by email"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    """Get user by ID"""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def save_typing_result(user_id, wpm, accuracy, test_duration):
    """Save typing test result"""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO typing_results (user_id, wpm, accuracy, test_duration) VALUES (?, ?, ?, ?)',
        (user_id, wpm, accuracy, test_duration)
    )
    
    # Update total tests count
    conn.execute(
        'UPDATE users SET total_tests = total_tests + 1 WHERE id = ?',
        (user_id,)
    )
    
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Get comprehensive user statistics"""
    conn = get_db_connection()
    
    # Get user info
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Get typing stats
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_tests,
            AVG(wpm) as avg_wpm,
            MAX(wpm) as best_wpm,
            AVG(accuracy) as avg_accuracy,
            MAX(accuracy) as best_accuracy
        FROM typing_results 
        WHERE user_id = ?
    ''', (user_id,)).fetchone()
    
    # Get recent results for chart
    recent_results = conn.execute('''
        SELECT wpm, accuracy, created_at
        FROM typing_results 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    # Get badges
    badges = conn.execute('''
        SELECT * FROM badges 
        WHERE user_id = ? 
        ORDER BY earned_at DESC
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return {
        'user': dict(user) if user else None,
        'total_tests': stats['total_tests'] if stats else 0,
        'avg_wpm': round(stats['avg_wpm'], 1) if stats and stats['avg_wpm'] else 0,
        'best_wpm': round(stats['best_wpm'], 1) if stats and stats['best_wpm'] else 0,
        'avg_accuracy': round(stats['avg_accuracy'], 1) if stats and stats['avg_accuracy'] else 0,
        'best_accuracy': round(stats['best_accuracy'], 1) if stats and stats['best_accuracy'] else 0,
        'current_streak': user['current_streak'] if user else 0,
        'longest_streak': user['longest_streak'] if user else 0,
        'recent_results': [dict(row) for row in recent_results] if recent_results else [],
        'badges': [dict(row) for row in badges] if badges else []
    }

def get_leaderboard():
    """Get leaderboard data"""
    conn = get_db_connection()
    
    leaders = conn.execute('''
        SELECT 
            u.id,
            u.name,
            u.current_streak,
            u.longest_streak,
            u.total_tests,
            COALESCE(MAX(tr.wpm), 0) as best_wpm,
            COALESCE(AVG(tr.accuracy), 0) as avg_accuracy,
            COALESCE(AVG(tr.wpm), 0) as avg_wpm
        FROM users u
        LEFT JOIN typing_results tr ON u.id = tr.user_id
        GROUP BY u.id
        HAVING u.total_tests > 0
        ORDER BY best_wpm DESC, avg_accuracy DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    return [dict(row) for row in leaders]

def get_all_users():
    """Get all users for dashboard display"""
    conn = get_db_connection()
    
    users = conn.execute('''
        SELECT 
            u.id,
            u.name,
            u.current_streak,
            u.total_tests,
            COALESCE(MAX(tr.wpm), 0) as best_wpm
        FROM users u
        LEFT JOIN typing_results tr ON u.id = tr.user_id
        GROUP BY u.id
        ORDER BY best_wpm DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    return [dict(row) for row in users]

def update_user_streak(user_id):
    """Update user's typing streak"""
    conn = get_db_connection()
    
    # Get user's last test date
    user = conn.execute('SELECT last_test_date, current_streak FROM users WHERE id = ?', (user_id,)).fetchone()
    
    today = date.today()
    last_test_date = datetime.strptime(user['last_test_date'], '%Y-%m-%d').date() if user['last_test_date'] else None
    
    if last_test_date:
        # Calculate days difference
        days_diff = (today - last_test_date).days
        
        if days_diff == 1:
            # Consecutive day - increment streak
            new_streak = user['current_streak'] + 1
        elif days_diff == 0:
            # Same day - no change
            new_streak = user['current_streak']
        else:
            # Streak broken - reset to 1
            new_streak = 1
    else:
        # First test ever
        new_streak = 1
    
    # Update user record
    conn.execute('''
        UPDATE users 
        SET current_streak = ?, 
            longest_streak = MAX(longest_streak, ?),
            last_test_date = ?
        WHERE id = ?
    ''', (new_streak, new_streak, today.isoformat(), user_id))
    
    conn.commit()
    conn.close()

def create_badge(user_id, title, description):
    """Create a badge using anybadge and store in database"""
    try:
        # Create badge directory if it doesn't exist
        badge_dir = '/tmp/badges' if os.name != 'nt' else 'badges'
        os.makedirs(badge_dir, exist_ok=True)
        
        # Generate badge filename
        filename = f"badge_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg"
        filepath = os.path.join(badge_dir, filename)
        
        # Create badge with anybadge
        badge = anybadge.Badge(
            label=title,
            value=description,
            default_color='gold',
            text_color='white'
        )
        badge.write_badge(filepath)
        
        # Save to database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO badges (user_id, badge_type, title, description, image_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, 'achievement', title, description, filepath))
        conn.commit()
        conn.close()
        
        return filepath
    except Exception as e:
        print(f"Error creating badge: {e}")
        return None