from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from threading import RLock
from uuid import uuid4

from backend.app.services.state_service import StateService


@dataclass(slots=True)
class SessionRecord:
    id: str
    selected_profile: str
    profile_source: str
    created_at: float

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


class SessionService:
    """Mantem sessoes leves; a camera ainda e compartilhada no MVP."""

    def __init__(self, state_service: StateService) -> None:
        self._state_service = state_service
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = RLock()

    def create(self) -> SessionRecord:
        session = SessionRecord(
            id=str(uuid4()),
            selected_profile=self._state_service.selected_profile_id(),
            profile_source="manual",
            created_at=time.time(),
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> SessionRecord | None:
        with self._lock:
            return self._sessions.get(session_id)

    def select_profile(self, session_id: str, profile_id: str) -> SessionRecord:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(session_id)

            profile = self._state_service.select_profile(profile_id)
            session.selected_profile = str(profile["id"])
            session.profile_source = "manual"
            return session
