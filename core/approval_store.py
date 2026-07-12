from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from threading import Lock
from typing import Any


@dataclass
class PendingAction:
    action_id: str
    tool: str
    arguments: dict[str, Any]
    preview: dict[str, Any]
    created_at: str
    expires_at: str


class ApprovalStore:
    """In-memory, single-use approval store for state-changing actions."""

    def __init__(self, ttl_minutes: int = 15) -> None:
        self.ttl_minutes = max(1, min(ttl_minutes, 60))
        self._items: dict[str, PendingAction] = {}
        self._lock = Lock()

    def create(
        self,
        tool: str,
        arguments: dict[str, Any],
        preview: dict[str, Any],
    ) -> PendingAction:
        now = datetime.now(timezone.utc)
        item = PendingAction(
            action_id=token_urlsafe(24),
            tool=tool,
            arguments=dict(arguments),
            preview=dict(preview),
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=self.ttl_minutes)).isoformat(),
        )
        with self._lock:
            self._purge_expired_locked(now)
            self._items[item.action_id] = item
        return item

    def peek(self, action_id: str) -> PendingAction | None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._purge_expired_locked(now)
            return self._items.get(action_id)

    def consume(self, action_id: str) -> PendingAction | None:
        """Remove and return an action so the same approval cannot be replayed."""
        now = datetime.now(timezone.utc)
        with self._lock:
            self._purge_expired_locked(now)
            return self._items.pop(action_id, None)

    def cancel(self, action_id: str) -> PendingAction | None:
        with self._lock:
            return self._items.pop(action_id, None)

    def serialize(self, item: PendingAction) -> dict[str, Any]:
        return asdict(item)

    def _purge_expired_locked(self, now: datetime) -> None:
        expired: list[str] = []
        for action_id, item in self._items.items():
            expires_at = datetime.fromisoformat(item.expires_at)
            if expires_at <= now:
                expired.append(action_id)
        for action_id in expired:
            self._items.pop(action_id, None)
