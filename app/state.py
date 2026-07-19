from __future__ import annotations

from pathlib import Path

from app.database import StateDatabase
from app.library import GameQueueItem, LibraryStore, QueueStore


class SQLiteLibraryStore(LibraryStore):
    """LibraryStore-compatible adapter backed by CacheDeck's SQLite database."""

    def __init__(self, database: StateDatabase) -> None:
        super().__init__(Path("cachedeck.db"))
        self.database = database

    def _read_unlocked(self) -> dict[str, object]:
        return {
            "last_refreshed_at": self.database.get_meta("library.last_refreshed_at"),
            "last_completed_job_id": self.database.get_meta("library.last_completed_job_id"),
            "last_activity_job_id": self.database.get_meta("library.last_activity_job_id"),
            "games": self.database.list_game_payloads(),
        }

    def _write_unlocked(self, raw: dict[str, object]) -> None:
        games = raw.get("games") if isinstance(raw.get("games"), list) else []
        self.database.replace_game_payloads(
            [item for item in games if isinstance(item, dict)]
        )
        for source, target in (
            ("last_refreshed_at", "library.last_refreshed_at"),
            ("last_completed_job_id", "library.last_completed_job_id"),
            ("last_activity_job_id", "library.last_activity_job_id"),
        ):
            value = raw.get(source)
            self.database.set_meta(target, str(value) if value else None)


class SQLiteQueueStore(QueueStore):
    """QueueStore-compatible adapter backed by CacheDeck's SQLite database."""

    def __init__(self, database: StateDatabase) -> None:
        super().__init__(Path("cachedeck.db"))
        self.database = database

    def _read_unlocked(self):
        result = []
        for item in self.database.list_queue_payloads():
            try:
                result.append(GameQueueItem.model_validate(item))
            except Exception:
                continue
        return result

    def _write_unlocked(self, items) -> None:
        self.database.replace_queue_payloads(
            [item.model_dump(mode="json") for item in items[-100:]]
        )
