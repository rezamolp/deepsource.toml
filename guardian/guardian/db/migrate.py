from __future__ import annotations

from .base import Base, create_session_factory
# Ensure models are imported so Base.metadata is populated
from . import models  # noqa: F401
from ..config import load_settings


def main() -> None:
    settings = load_settings()
    SessionLocal, engine = create_session_factory(settings.database_url)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
