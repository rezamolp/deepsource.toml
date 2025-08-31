#!/bin/bash
# پاک کردن cache ها
rm -rf .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# اجرای تست‌ها از ریشه پروژه
cd "$(dirname "$0")"
pytest --cache-clear -q
