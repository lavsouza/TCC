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
    ) -> None:
        self._host = host
        self._port = port
        self._directory = directory
        self._ws_url = ws_url
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def start(self) -> None:
        if self._server is not None:
            return

        handler = partial(
            _StrudelRequestHandler,
            directory=str(self._directory),
            ws_url=self._ws_url,
        )
        self._server = ThreadingHTTPServer((self._host, self._port), handler)
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
