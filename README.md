# ⚡ TaskEarner – Task & Job Earning Platform

A production-ready Flask web application where users earn money by completing simple online tasks, with a full admin panel for managing users, tasks, submissions, and withdrawals.

---

## 🚀 Features

### User Side
- ✅ Email OTP registration & verification
- ✅ Secure login with Remember Me
- ✅ Forgot/reset password via email OTP
- ✅ Dashboard with wallet, stats, submissions
- ✅ Browse & filter tasks by category
- ✅ Submit proof screenshots for tasks
- ✅ Wallet with full transaction history
- ✅ UPI withdrawal requests
- ✅ Referral system with bonus rewards
- ✅ Profile management with photo upload
- ✅ Dark / Light mode

### Admin Panel
- ✅ Separate admin login (session-based)
- ✅ Dashboard analytics
- ✅ User management (view, search, ban/unban, verify)
- ✅ Task CRUD (create, edit, delete, toggle)
- ✅ Review submissions (approve/reject with reason)
- ✅ Process withdrawals (approve/reject + refund)
- ✅ Email notifications for all key events

---

## 🛠 Tech Stack

| Layer       | Technology                   |
|-------------|------------------------------|
| Backend     | Flask 3.x (Python)           |
| Database    | SQLAlchemy + SQLite (default)|
| Frontend    | Bootstrap 5.3, Vanilla JS    |
| Auth        | Flask-Login + Werkzeug       |
| Forms       | Flask-WTF (CSRF protected)   |
| Email       | Flask-Mail (Gmail SMTP)      |
| Migrations  | Flask-Migrate (Alembic)      |
| Rate limit  | Flask-Limiter                |
| Images      | Pillow                       |

---

## 📁 Project Structure

```
taskearner/
├── run.py                    # Entry point
├── config.py                 # Config classes
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py           # App factory
│   ├── models.py             # All DB models
│   ├── auth/                 # Auth blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── user/                 # User dashboard blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── admin/                # Admin panel blueprint
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   ├── main/                 # Landing page blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── utils/
│   │   ├── email.py          # Email helpers
│   │   └── helpers.py        # File upload, pagination
│   ├── templates/
│   │   ├── base.html
│   │   ├── main/
│   │   ├── auth/
│   │   ├── user/
│   │   ├── admin/
│   │   └── emails/
│   └── static/
│       ├── css/
│       ├── js/
│       ├── img/
│       └── uploads/
│           ├── profiles/
│           └── proofs/
```

---

## ⚙️ Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### 1 — Clone & enter the directory
```bash
git clone https://github.com/tyagirtk-dev/taskearning.git
cd taskearner
```

### 2 — Create & activate virtualenv
```bash
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate.bat       # Windows
```

### 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### 4 — Configure environment
```bash
cp .env.example .env
nano .env       # fill in your values
```

Key values to set:
| Variable | Description |
|---|---|
| `SECRET_KEY` | Random secret (use `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `MAIL_USERNAME` | Your Gmail address |
| `MAIL_PASSWORD` | Gmail **App Password** (not your login password) |
| `ADMIN_EMAIL` | Initial admin email |
| `ADMIN_PASSWORD` | Initial admin password |

> **Gmail App Password**: Go to Google Account → Security → 2-Step Verification → App passwords → Generate one for "Mail".

### 5 — Run the development server
```bash
python run.py
```
Visit `http://localhost:5000`

---

## 📱 Termux (Android) Installation

```bash
pkg update && pkg upgrade -y
pkg install python git -y
pip install --upgrade pip

git clone https://github.com/tyagirtk-dev/taskearning.git
cd taskearner
pip install -r requirements.txt
cp .env.example .env
nano .env          # configure your values
python run.py
```

---

## 🏭 Production Deployment

### With Gunicorn + Nginx

```bash
# Install gunicorn (already in requirements.txt)
gunicorn -w 4 -b 127.0.0.1:5000 "run:app"

# Set FLASK_ENV=production in your .env
```

### Switch to MySQL
1. Install: `pip install pymysql`
2. Set in `.env`:
   ```
   DATABASE_URL=mysql+pymysql://user:password@localhost/taskearner
   ```
3. Run migrations:
   ```bash
   flask db init
   flask db migrate -m "initial"
   flask db upgrade
   ```

---

## 🔑 Default Admin Credentials

Set in `.env` — defaults are:
- Email: `admin@taskearner.com`
- Password: `Admin@123456`

**Change these before deploying to production.**

Admin panel URL: `/admin/login`

---

## 🗄️ Database Models

| Model | Purpose |
|---|---|
| `User` | Platform users, wallet, referral |
| `Admin` | Admin panel accounts |
| `Task` | Task definitions |
| `TaskSubmission` | User task submissions + proof |
| `WalletTransaction` | Credit/debit ledger |
| `WithdrawalRequest` | UPI withdrawal requests |
| `EmailVerificationToken` | OTP tokens (verify + reset) |

---

## 🔒 Security Features

- Werkzeug password hashing (PBKDF2-SHA256)
- CSRF protection on all forms (Flask-WTF)
- Rate limiting on auth endpoints (Flask-Limiter)
- Secure file upload (extension whitelist + Pillow resize)
- Session-based admin auth (separate from user auth)
- Email enumeration prevention on password reset
- XSS protection via Jinja2 auto-escaping
- `HttpOnly` & `SameSite=Lax` session cookies

---

## 📧 Email Notifications Sent

| Event | Recipient |
|---|---|
| Registration OTP | User |
| Welcome message | User |
| Password reset OTP | User |
| Task approved | User |
| Task rejected | User |
| Withdrawal approved | User |
| Withdrawal rejected | User |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push & open a PR

---

## 📄 License

MIT License — free to use, modify, and distribute.
