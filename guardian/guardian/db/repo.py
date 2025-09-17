from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Tuple

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .models import Event, RotationLog, SettingKV


@dataclass
class WindowCount:
    total_count: int
    window_seconds: int
    threshold: int


class Repository:
    def __init__(self, session: Session):
        self.session = session

    # Settings
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        kv = self.session.get(SettingKV, key)
        return kv.value if kv else default

    def set_setting(self, key: str, value: str) -> None:
        kv = self.session.get(SettingKV, key)
        if kv is None:
            kv = SettingKV(key=key, value=value)
            self.session.add(kv)
        else:
            kv.value = value
        self.session.commit()

    # Events
    def prune_events(self, chat_id: int, kind: str, window_seconds: int) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        self.session.query(Event).filter(
            Event.chat_id == chat_id,
            Event.kind == kind,
            Event.ts < cutoff,
        ).delete(synchronize_session=False)
        self.session.commit()

    def add_event(self, chat_id: int, kind: str, count: int, trace_id: Optional[str]) -> None:
        self.session.add(Event(chat_id=chat_id, kind=kind, count=count, trace_id=trace_id))
        self.session.commit()

    def window_count(self, chat_id: int, kind: str, window_seconds: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        stmt: Select = select(func.coalesce(func.sum(Event.count), 0)).where(
            Event.chat_id == chat_id,
            Event.kind == kind,
            Event.ts >= cutoff,
        )
        return int(self.session.execute(stmt).scalar_one())

    def last_events(self, limit: int = 10) -> List[Event]:
        stmt = select(Event).order_by(Event.ts.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    # Rotation logs
    def add_rotation_log(self, chat_id: int, result: str, reason: str, new_link: Optional[str], trace_id: Optional[str]) -> None:
        self.session.add(RotationLog(chat_id=chat_id, result=result, reason=reason, new_link=new_link, trace_id=trace_id))
        self.session.commit()

    def last_rotations(self, limit: int = 10) -> List[RotationLog]:
        stmt = select(RotationLog).order_by(RotationLog.ts.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())
