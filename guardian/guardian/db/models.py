from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(default=utcnow)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    kind: Mapped[str] = mapped_column(String(16))  # 'join' | 'view'
    count: Mapped[int] = mapped_column(Integer)
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_events_chat_kind_ts", "chat_id", "kind", "ts"),
    )


class RotationLog(Base):
    __tablename__ = "rotation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(default=utcnow)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    result: Mapped[str] = mapped_column(String(16))  # 'ok' | 'fail'
    reason: Mapped[str] = mapped_column(String(32))  # 'join_burst' | 'view_burst' | 'manual' | 'test'
    new_link: Mapped[Optional[str]] = mapped_column(String(256))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_rotation_chat_ts", "chat_id", "ts"),
    )


class SettingKV(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(String(256))
