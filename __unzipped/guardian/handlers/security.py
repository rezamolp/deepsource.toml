import time

user_hits = {}

def is_rate_limited(user_id, limit=3, window=5):
    now = time.time()
    hits = user_hits.get(user_id, [])
    hits = [t for t in hits if now - t < window]
    hits.append(now)
    user_hits[user_id] = hits
    return len(hits) > limit
