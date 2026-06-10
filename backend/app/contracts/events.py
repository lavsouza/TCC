from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = "1.0"


class EventEnvelope(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    type: str
    timestamp: float = Field(default_factory=time.time)
    session_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ClientEvent(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    type: str
    data: dict[str, Any] = Field(default_factory=dict)


def make_event(
    event_type: str,
    data: dict[str, Any],
    *,
    session_id: str | None = None,
) -> EventEnvelope:
    return EventEnvelope(type=event_type, data=data, session_id=session_id)
