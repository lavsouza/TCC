from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.config import ApiSettings
from backend.app.services.capture_runtime import CaptureRuntime
from backend.app.services.realtime_hub import RealtimeHub
from backend.app.services.session_service import SessionService
from backend.app.services.state_service import StateService
from utils.config import load_config


def create_app(
    settings: ApiSettings | None = None,
    *,
    capture_runtime: CaptureRuntime | None = None,
) -> FastAPI:
    resolved_settings = settings or ApiSettings()
    domain_config = load_config()
    state_service = StateService(domain_config)
    realtime_hub = RealtimeHub()
    session_service = SessionService(state_service)
    runtime = capture_runtime
    if runtime is None and resolved_settings.capture_enabled:
        runtime = CaptureRuntime(domain_config.camera, state_service, realtime_hub)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        realtime_hub.bind_loop(asyncio.get_running_loop())
        if runtime is not None:
            runtime.start()
        yield
        if runtime is not None:
            runtime.stop()
        realtime_hub.unbind_loop()

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.api_version,
        description=(
            "API de captura corporal, mapeamento musical e streaming de estado "
            "para o frontend Strudel."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    app.state.settings = resolved_settings
    app.state.state_service = state_service
    app.state.session_service = session_service
    app.state.realtime_hub = realtime_hub
    app.state.capture_runtime = runtime
    return app


app = create_app()


def run() -> None:
    settings = ApiSettings()
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
