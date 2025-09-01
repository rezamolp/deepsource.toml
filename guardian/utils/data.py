import json
import os

DATA_FILE = "data.json"

def load_data() -> dict:
    """خواندن داده‌ها از فایل JSON ساده"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data: dict):
    """ذخیره‌سازی داده‌ها در فایل JSON ساده"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
