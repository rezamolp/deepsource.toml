import logging

logger = logging.getLogger(__name__)

async def handle_error(update, exception):
    trace_id = getattr(update, 'update_id', None) or "unknown"
    chat_id = update.effective_chat.id if update and update.effective_chat else "unknown"
    logger.error("❌ خطا", extra={"trace_id": trace_id, "chat_id": chat_id, "error": str(exception)})

async def log_warning(update, msg):
    trace_id = getattr(update, 'update_id', None) or "unknown"
    chat_id = update.effective_chat.id if update and update.effective_chat else "unknown"
    logger.warning(msg, extra={"trace_id": trace_id, "chat_id": chat_id})

async def log_info(update, msg):
    trace_id = getattr(update, 'update_id', None) or "unknown"
    chat_id = update.effective_chat.id if update and update.effective_chat else "unknown"
    logger.info(msg, extra={"trace_id": trace_id, "chat_id": chat_id})


import logging
logger = logging.getLogger(__name__)

async def log_handler_error(message, trace_id: str | None = None, step: str | None = None):
    logger.error("handler_error", extra={
        "trace_id": trace_id or "unknown",
        "step": step or "unknown",
        "payload": getattr(message, "text", None),
        "user_id": getattr(message.from_user, "id", "unknown"),
    })
