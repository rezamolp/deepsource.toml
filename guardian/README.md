# Guardian Anti-Spam Bot for Telegram Channels

Production-grade anti-spam for Telegram channels: detects join/view bursts and rotates the public link (username) automatically, falling back to a private invite link.

## Features
- Join-burst and view-burst detection (defaults: Join 10/60s, View +50/60s on last 3 posts)
- Username rotation `guardian` -> `guardian1..guardian100` -> private invite
- Concurrency guard: single rotation per 2 seconds
- Admin bot (aiogram) with status, settings, logs, test, Telethon login FSM
- SQLite with SQLAlchemy; pruning old records; composite indexes
- JSON logs to stdout; health server on :8080/healthz
- Unit tests with pytest

## Setup

1) Create `.env` from example and fill values:

```bash
cp .env.example .env
```

Required:
- `BOT_TOKEN`, `ADMIN_ID`, `API_ID`, `API_HASH`, `TARGET_CHAT_ID`

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Initialize DB:

```bash
python -m guardian.db.migrate
```

4) Run:

```bash
python -m guardian.main
```

5) Healthcheck:

```bash
curl -s http://localhost:8080/healthz
```

Grant the bot admin rights in your target channel. The Telethon session is stored under `sessions/`.

## Testing

```bash
pytest -q
```

## Security Notes
- No secrets are logged; sensitive fields are masked
- Store secrets only in `.env`
- Restrict the admin bot to your `ADMIN_ID`
