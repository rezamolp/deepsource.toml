@echo off
echo 🚀 Guardian Anti-Spam Bot Installer (Windows)

:: 1. ساخت venv
if not exist venv (
  echo 📦 Creating virtualenv...
  python -m venv venv
)

:: 2. فعال‌سازی venv
call venv\Scripts\activate

:: 3. نصب وابستگی‌ها
echo 📦 Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

:: 4. ساخت .env اگر نبود
if not exist .env (
  echo ⚠️  .env not found → copying from .env.example
  copy .env.example .env
  echo 👉 Please edit .env and set BOT_TOKEN, API_ID, API_HASH, ADMIN_ID
)

:: 5. اجرای migration
echo 🗄 Running DB migration...
sqlite3 guardian.db < storage/migrations/001_init.sql

:: 6. اجرای تست‌ها
echo 🧪 Running tests...
pytest -v --maxfail=1 --disable-warnings

:: 7. اجرای ربات
echo 🤖 Starting Guardian Bot...
python runner.py
