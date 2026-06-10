from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.app.contracts.api import (
    CatalogResponse,
    HealthResponse,
    ProfileSelectionRequest,
    SessionResponse,
)
from backend.app.contracts.events import ClientEvent, make_event


router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    runtime = request.app.state.capture_runtime
    capture = runtime.status() if runtime is not None else {
        "enabled": False,
        "running": False,
        "last_error": None,
        "frames_processed": 0,
    }
    return HealthResponse(
        status="ok" if capture["last_error"] is None else "degraded",
        api_version=request.app.state.settings.api_version,
        capture=capture,
    )


@router.get("/catalog", response_model=CatalogResponse)
def catalog(request: Request) -> CatalogResponse:
    state_service = request.app.state.state_service
    return CatalogResponse(
        default_profile_id=state_service.default_profile_id(),
        profiles=state_service.catalog(),
    )


@router.get("/profiles")
def profiles(request: Request) -> list[dict[str, object]]:
    return request.app.state.state_service.catalog()


@router.get("/profiles/{profile_id}")
def profile(profile_id: str, request: Request) -> dict[str, object]:
    try:
        return request.app.state.state_service.get_profile(profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(request: Request) -> SessionResponse:
    session = request.app.state.session_service.create()
    return SessionResponse(**session.to_payload())


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, request: Request) -> SessionResponse:
    session = request.app.state.session_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.")
    return SessionResponse(**session.to_payload())


@router.patch(
    "/sessions/{session_id}/profile",
    response_model=SessionResponse,
)
def select_profile(
    session_id: str,
    selection: ProfileSelectionRequest,
    request: Request,
) -> SessionResponse:
    try:
        session = request.app.state.session_service.select_profile(
            session_id,
            selection.profile_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sessao nao encontrada.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return SessionResponse(**session.to_payload())


@router.websocket("/sessions/{session_id}/stream")
async def session_stream(websocket: WebSocket, session_id: str) -> None:
    app = websocket.app
    session_service = app.state.session_service
    hub = app.state.realtime_hub
    session = session_service.get(session_id)
    if session is None:
        await websocket.close(code=4404, reason="Sessao nao encontrada.")
        return

    await hub.connect(session_id, websocket)
    await websocket.send_json(
        make_event(
            "session.status.v1",
            {"status": "connected", "session": session.to_payload()},
            session_id=session_id,
        ).model_dump(mode="json")
    )

    try:
        while True:
            raw_event = await websocket.receive_json()
            try:
                event = ClientEvent.model_validate(raw_event)
            except ValidationError as exc:
                await websocket.send_json(
                    make_event(
                        "error.v1",
                        {"code": "invalid_event", "detail": str(exc)},
                        session_id=session_id,
                    ).model_dump(mode="json")
                )
                continue

            if event.type != "profile.select.v1":
                await websocket.send_json(
                    make_event(
                        "error.v1",
                        {
                            "code": "unsupported_event",
                            "detail": f"Evento nao suportado: {event.type}",
                        },
                        session_id=session_id,
                    ).model_dump(mode="json")
                )
                continue

            profile_id = event.data.get("profile_id")
            if not isinstance(profile_id, str):
                await websocket.send_json(
                    make_event(
                        "error.v1",
                        {
                            "code": "invalid_profile",
                            "detail": "profile_id deve ser texto.",
                        },
                        session_id=session_id,
                    ).model_dump(mode="json")
                )
                continue

            try:
                updated = session_service.select_profile(session_id, profile_id)
            except ValueError as exc:
                await websocket.send_json(
                    make_event(
                        "error.v1",
                        {"code": "invalid_profile", "detail": str(exc)},
                        session_id=session_id,
                    ).model_dump(mode="json")
                )
                continue

            await websocket.send_json(
                make_event(
                    "profile.selected.v1",
                    {"session": updated.to_payload()},
                    session_id=session_id,
                ).model_dump(mode="json")
            )
    except WebSocketDisconnect:
        hub.disconnect(session_id, websocket)
