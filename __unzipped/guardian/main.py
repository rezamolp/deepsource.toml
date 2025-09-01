import signal
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ChatMemberHandler, filters
from config import BOT_TOKEN, ADMIN_ID
from handlers.commands import start
from handlers.callbacks import button_handler
from handlers.messages import handle_text
from handlers.members import member_update
from utils.logger import setup_logger
from telegram import error as tg_error

setup_logger()
logger = logging.getLogger(__name__)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["admin_id"] = ADMIN_ID

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(ChatMemberHandler(member_update, ChatMemberHandler.CHAT_MEMBER))

    # Global error handler
    async def on_error(update, context):
        import traceback, uuid
        trace_id = str(uuid.uuid4())
        err = context.error
        details = getattr(err, 'message', str(err))
        logger.error('telegram_error', extra={'event':'error','trace_id':trace_id,'details':details})
        try:
            if update and getattr(update, 'effective_chat', None):
                await context.bot.send_message(update.effective_chat.id, '❗ خطای موقت رخ داد. دوباره تلاش کنید.')
        except Exception:
            pass
    app.add_error_handler(on_error)

    logger.info("bot_started", extra={"event":"bot_started"})

    # Healthcheck server
    import threading, http.server, socketserver
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

    app.run_polling(stop_signals=[signal.SIGTERM, signal.SIGINT])

if __name__ == "__main__":
    main()
