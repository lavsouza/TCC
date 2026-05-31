from __future__ import annotations

import json
import threading
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class StrudelWebServer:
    def __init__(
        self,
        host: str,
        port: int,
        directory: Path,
        ws_url: str,
        port_search_span: int = 20,
    ) -> None:
        self._host = host
        self._preferred_port = port
        self._port = port
        self._port_search_span = max(port_search_span, 0)
        self._directory = directory
        self._ws_url = ws_url
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def set_ws_url(self, ws_url: str) -> None:
        self._ws_url = ws_url

    def start(self) -> None:
        if self._server is not None:
            return

        handler = partial(
            _StrudelRequestHandler,
            directory=str(self._directory),
            ws_url=self._ws_url,
        )
        last_error: OSError | None = None
        for candidate_port in _iter_candidate_ports(self._preferred_port, self._port_search_span):
            try:
                self._server = ThreadingHTTPServer((self._host, candidate_port), handler)
                self._port = candidate_port
                break
            except OSError as exc:
                last_error = exc

        if self._server is None:
            message = (
                f"Servidor HTTP do Strudel nao conseguiu abrir uma porta a partir de {self._preferred_port}"
            )
            if last_error is not None:
                raise RuntimeError(f"{message}: {last_error}") from last_error
            raise RuntimeError(message)

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="strudel-http-server",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        self._server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None


class _StrudelRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, ws_url: str, **kwargs) -> None:
        self._ws_url = ws_url
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/config.json":
            payload = {"wsUrl": self._ws_url}
            body = json.dumps(payload).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        return super().do_GET()

    def log_message(self, format: str, *args) -> None:
        del format, args


def _iter_candidate_ports(start_port: int, span: int) -> list[int]:
    return [start_port + offset for offset in range(span + 1)]
