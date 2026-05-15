from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

import websockets


class StrudelBridgeServer:
    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._clients: set[Any] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server_ready = threading.Event()
        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None
        self._stop_event: asyncio.Event | None = None

    def start(self) -> None:
        if self._thread is not None:
            return

        self._thread = threading.Thread(
            target=self._run_server_loop,
            name="strudel-websocket-server",
            daemon=True,
        )
        self._thread.start()
        if not self._server_ready.wait(timeout=5):
            raise RuntimeError("Servidor WebSocket do Strudel nao iniciou a tempo.")

    def publish(self, payload: dict[str, object]) -> None:
        if self._loop is None or self._stop_requested.is_set():
            return

        message = json.dumps(payload)
        future = asyncio.run_coroutine_threadsafe(
            self._broadcast(message),
            self._loop,
        )
        try:
            future.result(timeout=1)
        except Exception:
            # Se o navegador nao estiver conectado, nao interrompemos o prototipo.
            return

    def stop(self) -> None:
        self._stop_requested.set()
        if self._loop is not None and self._stop_event is not None:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def _run_server_loop(self) -> None:
        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        self._stop_event = asyncio.Event()

        try:
            loop.run_until_complete(self._run_server())
        finally:
            loop.run_until_complete(self._close_clients())
            loop.close()
            self._loop = None

    async def _run_server(self) -> None:
        async with websockets.serve(self._handle_client, self._host, self._port):
            self._server_ready.set()
            assert self._stop_event is not None
            await self._stop_event.wait()

    async def _handle_client(self, websocket) -> None:
        self._clients.add(websocket)
        try:
            async for _ in websocket:
                pass
        finally:
            self._clients.discard(websocket)

    async def _broadcast(self, message: str) -> None:
        stale_clients: list[Any] = []
        for client in tuple(self._clients):
            try:
                await client.send(message)
            except Exception:
                stale_clients.append(client)

        for client in stale_clients:
            self._clients.discard(client)

    async def _close_clients(self) -> None:
        for client in tuple(self._clients):
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()
