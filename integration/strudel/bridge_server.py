from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import Callable
from typing import Any

import websockets


class StrudelBridgeServer:
    def __init__(
        self,
        host: str,
        port: int,
        port_search_span: int = 20,
        message_handler: Callable[[dict[str, object]], None] | None = None,
    ) -> None:
        self._host = host
        self._preferred_port = port
        self._port = port
        self._port_search_span = max(port_search_span, 0)
        self._message_handler = message_handler
        self._clients: set[Any] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server_ready = threading.Event()
        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None
        self._stop_event: asyncio.Event | None = None
        self._startup_error: Exception | None = None

    @property
    def port(self) -> int:
        return self._port

    @property
    def ws_url(self) -> str:
        return f"ws://{self._host}:{self._port}"

    def start(self) -> None:
        if self._thread is not None:
            return

        self._server_ready.clear()
        self._stop_requested.clear()
        self._startup_error = None
        self._thread = threading.Thread(
            target=self._run_server_loop,
            name="strudel-websocket-server",
            daemon=True,
        )
        self._thread.start()
        if not self._server_ready.wait(timeout=5):
            self.stop()
            raise RuntimeError("Servidor WebSocket do Strudel nao iniciou a tempo.")

        if self._startup_error is not None:
            startup_error = self._startup_error
            self.stop()
            raise RuntimeError(
                f"Servidor WebSocket do Strudel nao conseguiu abrir uma porta a partir de {self._preferred_port}: {startup_error}"
            ) from startup_error

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
        except Exception as exc:
            self._startup_error = exc
            self._server_ready.set()
        finally:
            loop.run_until_complete(self._close_clients())
            loop.close()
            self._loop = None

    async def _run_server(self) -> None:
        last_error: Exception | None = None
        for candidate_port in _iter_candidate_ports(self._preferred_port, self._port_search_span):
            try:
                async with websockets.serve(
                    self._handle_client,
                    self._host,
                    candidate_port,
                ):
                    self._port = candidate_port
                    self._server_ready.set()
                    assert self._stop_event is not None
                    await self._stop_event.wait()
                    return
            except OSError as exc:
                last_error = exc

        if last_error is None:
            raise RuntimeError("Nenhuma porta candidata foi gerada para o WebSocket.")
        raise last_error

    async def _handle_client(self, websocket) -> None:
        self._clients.add(websocket)
        try:
            async for message in websocket:
                self._dispatch_message(message)
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

    def _dispatch_message(self, message: str) -> None:
        if self._message_handler is None:
            return

        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return

        if not isinstance(payload, dict):
            return

        try:
            self._message_handler(payload)
        except Exception:
            return


def _iter_candidate_ports(start_port: int, span: int) -> list[int]:
    return [start_port + offset for offset in range(span + 1)]
