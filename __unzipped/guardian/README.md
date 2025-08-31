
## 🟢 Activation Checklist
1. پر کردن فایل `.env` (BOT_TOKEN, API_ID, API_HASH, ADMIN_ID).
2. اجرای migration: `sqlite3 guardian.db < storage/migrations/001_init.sql`
3. تنظیم BotFather: Privacy Mode = Disabled.
4. افزودن ربات به کانال و دادن دسترسی Admin.
5. تست healthcheck: `curl http://localhost:8080/healthz`

## 🚦 Preflight & Activation Checklist
1. مقادیر `.env` را کامل کنید: BOT_TOKEN, API_ID, API_HASH, ADMIN_ID.
2. اجرای migration: `sqlite3 guardian.db < storage/migrations/001_init.sql`.
3. در BotFather:
   - دستور `/setprivacy` → Disabled.
   - دستور `/setjoingroups` → Enabled.
4. ربات را به کانال اضافه کنید و دسترسی Admin بدهید.
5. تست healthcheck: `curl http://localhost:8080/healthz`.
6. مانیتور لاگ‌ها از stdout (JSON). مطمئن شوید لاگ‌ها شامل ts, chat_id, trace_id هستند.

## 🚦 Preflight & Activation Checklist (RC)
1. فایل `.env` را پر کنید: BOT_TOKEN, API_ID, API_HASH, ADMIN_ID, JOIN_THRESHOLD, JOIN_WINDOW.
2. اجرای migration: `sqlite3 guardian.db < storage/migrations/001_init.sql`
3. در BotFather:
   - `/setprivacy` → Disabled.
   - `/setjoingroups` → Enabled.
4. ربات را به کانال اضافه و Admin کنید.
5. Healthcheck: `curl http://localhost:8080/healthz`
6. مانیتورینگ: لاگ‌ها را در stdout (JSON) بخوانید؛ حتماً شامل trace_id, chat_id باشند.

## ✅ Final Activation Checklist (Production)
1. فایل `.env` را پر کنید: BOT_TOKEN, API_ID, API_HASH, ADMIN_ID, JOIN_THRESHOLD, JOIN_WINDOW.
2. اجرای migration: `sqlite3 guardian.db < storage/migrations/001_init.sql`
3. در BotFather:
   - `/setprivacy` → Disabled.
   - `/setjoingroups` → Enabled.
4. ربات را به کانال اضافه و دسترسی Admin بدهید.
5. Healthcheck: `curl http://localhost:8080/healthz`
6. مانیتورینگ: لاگ‌های JSON stdout را چک کنید (ts, chat_id, trace_id الزامی).
7. تست‌های واحد: `pytest -v --maxfail=1 --disable-warnings` و انتظار پوشش ≥80٪.

## 🚀 Production Activation Checklist
1. فایل `.env` را کامل کنید: BOT_TOKEN, API_ID, API_HASH, ADMIN_ID, JOIN_THRESHOLD, JOIN_WINDOW.
2. اجرای migration: `sqlite3 guardian.db < storage/migrations/001_init.sql`
3. در BotFather:
   - `/setprivacy` → Disabled
   - `/setjoingroups` → Enabled
4. ربات را به کانال اضافه و Admin کنید.
5. Healthcheck: `curl http://localhost:8080/healthz`
6. مانیتورینگ: لاگ‌های JSON stdout (ts, chat_id, trace_id, result) بررسی شوند.
7. تست‌ها: `pytest -v` و پوشش باید ≥80% باشد.

## 🛠 Runbook: Handling Link Rotation Issues
If public username rotation fails (exhaustion):
1. Check bot has **admin rights** on channel.
2. Inspect logs for `trace_id`.
3. If invite fallback is active → share new invite with members.
4. Reset base username in config if needed.

### Sample JSON Log (Rotation)
```json
{
  "event": "burst_detected",
  "chat_id": "12345",
  "kind": "join",
  "count": 12,
  "threshold": 10,
  "window_seconds": 60,
  "avg_rate": 0.2,
  "action": "rotate_link",
  "trace_id": "abc123",
  "user_id": "8270276130",
  "ts": "2025-08-30T12:34:56Z"
}
```
