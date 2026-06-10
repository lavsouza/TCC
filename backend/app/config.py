from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCB_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "MoveCodeBeats API"
    api_version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    capture_enabled: bool = True
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
