-- Added composite index for performance (P2)
CREATE INDEX IF NOT EXISTS idx_events_chat_kind_ts
ON events(chat_id, kind, ts);

-- Vacuum/Analyze recommended after migration
VACUUM;
ANALYZE;
