import time
from collections import deque
from config import SHORT_WINDOW, LONG_WINDOW, JOIN_LIMIT
from services.channel import change_public_link
from services.antispam_lock import acquire as acquire_lock

join_times = deque()
antispam_enabled = True

async def check_new_member(context, channel_id, base_username):
    global join_times, antispam_enabled
    if not antispam_enabled or not channel_id:
        return

    now = time.time()
    join_times.append(now)

    while join_times and now - join_times[0] > LONG_WINDOW:
        join_times.popleft()

    short_count = sum(1 for t in join_times if now - t <= SHORT_WINDOW)
    long_count = len(join_times)

    if short_count >= JOIN_LIMIT or long_count >= JOIN_LIMIT:
        if not acquire_lock(channel_id, 'join'):
            return
        await change_public_link(channel_id, base_username)
        await context.bot.send_message(
            chat_id=context.bot_data.get("admin_id"),
            text=f"⚠️ ضداسپم فعال شد! {short_count if short_count >= JOIN_LIMIT else long_count} عضو اضافه شدند.",
        )
        join_times.clear()


def log_burst(chat_id: int, kind: str, count: int, threshold: int, window: int, trace_id: str | None = None):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("burst_detected", extra={
        "event": "burst_detected",
        "chat_id": chat_id,
        "kind": kind,
        "count": count,
        "threshold": threshold,
        "window": window,
        "trace_id": trace_id or "unknown",
        "action": "rotate"
    })
