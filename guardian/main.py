import signal
import logging
from logging.handlers import RotatingFileHandler
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ChatMemberHandler, filters
from config import BOT_TOKEN, ADMIN_ID
from handlers.commands import start
from handlers.callbacks import button_handler
from handlers.messages import handle_text
from handlers.members import member_update

# تنظیم لاگر برای نمایش در CMD و ذخیره در فایل با محدودیت حجم 1MB
log_handler = RotatingFileHandler("bot.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        log_handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["admin_id"] = ADMIN_ID

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))

    logger.info("🤖 ربات ضداسپم اجرا شد...")
    app.run_polling(stop_signals=[signal.SIGTERM, signal.SIGINT])

if __name__ == "__main__":
    main()

# Phase4: add healthz endpoint
import threading, http.server, socketserver

def _start_healthz():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/healthz':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
            else:
                self.send_response(404)
                self.end_headers()
    threading.Thread(target=lambda: socketserver.TCPServer(('0.0.0.0',8080),Handler).serve_forever(),daemon=True).start()

_start_healthz()
