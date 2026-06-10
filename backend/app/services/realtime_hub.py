from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Iterable

from fastapi import WebSocket

from backend.app.contracts.events import EventEnvelope


class RealtimeHub:
    """Distribui eventos do thread de captura para clientes WebSocket."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def unbind_loop(self) -> None:
        self._loop = None

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[session_id].add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        clients = self._connections.get(session_id)
        if clients is None:
            return
        clients.discard(websocket)
        if not clients:
            self._connections.pop(session_id, None)

    def publish_from_capture(self, event: EventEnvelope) -> None:
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(self.broadcast(event))
        )

    async def broadcast(self, event: EventEnvelope) -> None:
        for session_id, clients in list(self._connections.items()):
            payload = event.model_copy(update={"session_id": session_id}).model_dump(
                mode="json"
            )
            await self._send_many(session_id, clients, payload)

    async def send_to_session(
        self,
        session_id: str,
        event: EventEnvelope,
    ) -> None:
        clients = self._connections.get(session_id, set())
        payload = event.model_copy(update={"session_id": session_id}).model_dump(
            mode="json"
        )
        await self._send_many(session_id, clients, payload)

    async def _send_many(
        self,
        session_id: str,
        clients: Iterable[WebSocket],
        payload: dict[str, object],
    ) -> None:
        stale: list[WebSocket] = []
        for client in list(clients):
            try:
                await client.send_json(payload)
            except Exception:
                stale.append(client)

        for client in stale:
            self.disconnect(session_id, client)
