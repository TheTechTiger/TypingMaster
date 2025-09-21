---

# ⌨️ Typing Speed Test Web App

A full‑stack **Flask-based typing speed test platform** with gamification, leaderboards, Google OAuth, motivational quotes, and text‑to‑speech feedback.  
Users can practice typing, track their progress, earn badges for milestones, and compete with others in real time.

🌐 **Live Demo:** [Typing Master on Vercel](https://typing-master-ebon.vercel.app/dashboard)  
📦 **Source Code:** [GitHub – TheTechTiger/TypingMaster](https://github.com/TheTechTiger/TypingMaster)

---

## 🚀 Features

- **User Authentication**
  - Email/password signup with email verification
  - Google OAuth login
  - Secure session management

- **Typing Test**
  - Randomized practice texts
  - Real‑time WPM & accuracy tracking
  - Configurable test durations

- **Gamification**
  - Streak tracking (daily practice rewards)
  - Badge generation for milestones (streaks & WPM records)
  - Motivational quotes after each test

- **Leaderboard**
  - Global ranking of top typists
  - User profile pages with personal stats

- **Text‑to‑Speech (TTS)**
  - Converts motivational quotes or results into speech
  - Uses Microsoft Edge TTS voices

- **Dashboard**
  - Personal stats (best WPM, accuracy, streaks)
  - Comparison with other users

---

## 🛠️ Tech Stack

- **Backend:** Flask (Python)  
- **Frontend:** Jinja2 templates (HTML, CSS, JS)  
- **Database:** SQLite (default, can be swapped)  
- **Auth:** Google OAuth + Email verification  
- **TTS:** [edge-tts](https://pypi.org/project/edge-tts/)  
- **Other:** Asyncio, Base64 encoding for audio  

---

## 📂 Project Structure

```
project/
│── app.py                # Main Flask app
│── database.py            # DB models & queries
│── auth.py                # Google OAuth & email verification
│── templates/             # HTML templates (index, dashboard, leaderboard, test)
│── static/                # CSS, JS, images
│── .env                   # Environment variables
│── requirements.txt       # Python dependencies
│── README.md              # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone the repo
```bash
git clone https://github.com/TheTechTiger/TypingMaster.git
cd TypingMaster
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables  
Create a `.env` file in the root directory:

```
SECRET_KEY=your-secret-key
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

> ⚠️ For Gmail, you’ll need an **App Password** (not your normal password).

### 5. Initialize the database
```bash
python -c "from database import init_db; init_db()"
```

### 6. Run the app
```bash
flask run
```

Visit: **http://127.0.0.1:5000/**

---

## 🏅 Badge System

- **Streak Badges:** Earned at 5, 10, 15, 30, 50, 100 days of continuous practice  
- **Speed Badges:**  
  - 40+ WPM → *Speed Boost*  
  - 60+ WPM → *Fast Typer*  
  - 80+ WPM → *Speed Demon*  
  - 100+ WPM → *Lightning Fingers*  

---

## 🔊 Text-to-Speech API

Endpoint:  
```http
POST /generate-speech
```

Payload:
```json
{ "text": "Keep going, you're improving every day!" }
```

Response:
```json
{ "success": true, "audio": "<base64-encoded-audio>" }
```

---

## 📊 API Endpoints (JSON)

- `POST /signup` → Create account  
- `POST /login` → Login with email/password  
- `POST /google-login` → Login with Google  
- `POST /submit-result` → Save typing test result  
- `GET /get-typing-stats` → Fetch user stats  
- `GET /leaderboard` → Leaderboard data  
- `GET /typing-text` → Random typing text  

---

## 🧩 Future Improvements

- Real‑time multiplayer typing races  
- Dark mode & customizable themes  
- Export stats as PDF/CSV  
- Mobile‑friendly PWA version  

---

## 🤝 Contributing

Pull requests are welcome!  
If you’d like to add new features (e.g., new badge types, multiplayer mode), fork the repo and submit a PR.

---

## 📜 License

MIT License – free to use, modify, and distribute.

---
