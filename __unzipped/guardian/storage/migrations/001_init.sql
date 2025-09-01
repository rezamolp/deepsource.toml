CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_chat_kind_ts ON events(chat_id, kind, ts);
