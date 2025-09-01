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
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

:: 3.1 Clean caches to avoid stale bytecode
echo 🧹 Cleaning caches...
for /r %%i in (__pycache__) do if exist "%%i" rd /s /q "%%i"
for /r %%i in (*.pyc) do del /q "%%i"
if exist .pytest_cache rd /s /q .pytest_cache
if exist .mypy_cache rd /s /q .mypy_cache

:: Build ID and file fingerprints
echo 🔎 Computing BUILD_ID...
set BUILD_ID=%DATE%_%TIME%
echo BUILD_ID=%BUILD_ID%
echo Python: %CD%\venv\Scripts\python.exe
echo Main:   %CD%\main.py

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
venv\Scripts\python.exe -m pytest -v --maxfail=1 --disable-warnings

:: 7. اجرای ربات
echo 🤖 Starting Guardian Bot...
venv\Scripts\python.exe runner.py
