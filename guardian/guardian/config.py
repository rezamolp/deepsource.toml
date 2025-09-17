from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    admin_fallback_chat_id: Optional[int]
    api_id: int
    api_hash: str
    target_chat_id: Optional[int]

    join_threshold: int = 10
    join_window_seconds: int = 60
    view_threshold: int = 50
    view_window_seconds: int = 60
    view_monitor_poll_seconds: int = 10

    rotation_base: str = "guardian"
    rotation_suffix_max: int = 100

    health_host: str = "0.0.0.0"
    health_port: int = 8080

    database_url: str = "sqlite:///guardian.sqlite3"

    log_level: str = "INFO"


def _int_env(name: str, default: Optional[int] = None) -> Optional[int]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid integer for env {name}: {value}")


def _str_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def load_settings() -> Settings:
    load_dotenv(override=False)

    bot_token = _str_env("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is required")

    admin_id = _int_env("ADMIN_ID")
    if admin_id is None:
        raise RuntimeError("ADMIN_ID is required")

    admin_fallback_chat_id = _int_env("ADMIN_FALLBACK_CHAT_ID")

    api_id = _int_env("API_ID")
    api_hash = _str_env("API_HASH")
    if api_id is None or not api_hash:
        raise RuntimeError("API_ID and API_HASH are required for Telethon")

    target_chat_id = _int_env("TARGET_CHAT_ID")

    join_threshold = _int_env("JOIN_THRESHOLD", 10) or 10
    join_window_seconds = _int_env("JOIN_WINDOW_SECONDS", 60) or 60
    view_threshold = _int_env("VIEW_THRESHOLD", 50) or 50
    view_window_seconds = _int_env("VIEW_WINDOW_SECONDS", 60) or 60
    view_monitor_poll_seconds = _int_env("VIEW_MONITOR_POLL_SECONDS", 10) or 10

    rotation_base = _str_env("ROTATION_BASE", "guardian") or "guardian"
    rotation_suffix_max = _int_env("ROTATION_SUFFIX_MAX", 100) or 100

    health_host = _str_env("HEALTH_HOST", "0.0.0.0") or "0.0.0.0"
    health_port = _int_env("HEALTH_PORT", 8080) or 8080

    database_url = _str_env("DATABASE_URL", "sqlite:///guardian.sqlite3") or "sqlite:///guardian.sqlite3"
    log_level = _str_env("LOG_LEVEL", "INFO") or "INFO"

    return Settings(
        bot_token=bot_token,
        admin_id=admin_id,
        admin_fallback_chat_id=admin_fallback_chat_id,
        api_id=api_id,
        api_hash=api_hash,
        target_chat_id=target_chat_id,
        join_threshold=join_threshold,
        join_window_seconds=join_window_seconds,
        view_threshold=view_threshold,
        view_window_seconds=view_window_seconds,
        view_monitor_poll_seconds=view_monitor_poll_seconds,
        rotation_base=rotation_base,
        rotation_suffix_max=rotation_suffix_max,
        health_host=health_host,
        health_port=health_port,
        database_url=database_url,
        log_level=log_level,
    )
