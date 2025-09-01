import os, sys, logging
from dotenv import load_dotenv

load_dotenv()

def _fail_fast(key: str, reason: str):
    msg = f'[CONFIG ERROR] {key}: {reason} | خطا در تنظیمات: {key} - {reason}'
    logging.critical(msg)
    sys.exit(1)

BOT_TOKEN = os.getenv('BOT_TOKEN') or _fail_fast('BOT_TOKEN','missing')
API_ID = int(os.getenv('API_ID') or _fail_fast('API_ID','missing'))
API_HASH = os.getenv('API_HASH') or _fail_fast('API_HASH','missing')
ADMIN_ID = int(os.getenv('ADMIN_ID') or _fail_fast('ADMIN_ID','missing'))
JOIN_THRESHOLD = int(os.getenv('JOIN_THRESHOLD','10'))
JOIN_WINDOW = int(os.getenv('JOIN_WINDOW','60'))
LOG_LEVEL = os.getenv('LOG_LEVEL','INFO')


# Added for antispam compatibility
SHORT_WINDOW = int(os.getenv('SHORT_WINDOW', JOIN_WINDOW))
LONG_WINDOW = int(os.getenv('LONG_WINDOW', JOIN_WINDOW * 6))
JOIN_LIMIT = int(os.getenv('JOIN_LIMIT', JOIN_THRESHOLD))
