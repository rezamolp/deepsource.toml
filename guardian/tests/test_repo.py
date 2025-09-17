from __future__ import annotations

from guardian.db.base import create_session_factory
from guardian.db.models import Base
from guardian.db.repo import Repository


def test_repo_event_prune_and_count(tmp_path):
    db_path = tmp_path / "test.sqlite3"
    SessionLocal, engine = create_session_factory(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    repo = Repository(SessionLocal())

    chat_id = -1001
    repo.add_event(chat_id, "join", 5, trace_id="t1")
    assert repo.window_count(chat_id, "join", 60) == 5
    repo.prune_events(chat_id, "join", 0)
    assert repo.window_count(chat_id, "join", 60) == 0
