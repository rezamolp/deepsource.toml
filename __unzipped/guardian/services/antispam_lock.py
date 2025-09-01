import time
from collections import defaultdict

_locks = defaultdict(float)

def acquire(chat_id: int, kind: str, ttl: float = 2.0) -> bool:
    key = (chat_id, kind)
    now = time.time()
    if _locks.get(key, 0) > now:
        return False
    _locks[key] = now + ttl
    return True
