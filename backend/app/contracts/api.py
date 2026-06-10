from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    api_version: str
    capture: dict[str, Any]


class ProfileSelectionRequest(BaseModel):
    profile_id: str = Field(min_length=1, max_length=32)


class SessionResponse(BaseModel):
    id: str
    selected_profile: str
    profile_source: str
    created_at: float


class CatalogResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    default_profile_id: str
    profiles: list[dict[str, Any]]
