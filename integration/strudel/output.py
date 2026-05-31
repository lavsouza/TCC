from __future__ import annotations

import webbrowser
from pathlib import Path

from integration.strudel.bridge_server import StrudelBridgeServer
from integration.strudel.preview_publisher import PreviewPublisher
from integration.strudel.publisher import StrudelPublisher
from integration.strudel.web_server import StrudelWebServer
from utils.config import PROJECT_ROOT, StrudelConfig
from utils.models import MotionFeatures, SoundParameters


class StrudelOutput:
    def __init__(self, config: StrudelConfig) -> None:
        self._config = config
        self._state_publisher = StrudelPublisher(config)
        self._preview_publisher = PreviewPublisher(config)
        self._bridge = StrudelBridgeServer(
            config.ws_host,
            config.ws_port,
            port_search_span=config.port_search_span,
        )
        self._web_server = StrudelWebServer(
            host=config.http_host,
            port=config.http_port,
            directory=Path(PROJECT_ROOT / "web" / "strudel"),
            ws_url=self._bridge.ws_url,
            port_search_span=config.port_search_span,
        )

    @property
    def enabled(self) -> bool:
        return self._config.enabled

    @property
    def web_url(self) -> str:
        return self._web_server.base_url

    def start(self) -> None:
        if not self.enabled:
            return

        try:
            self._bridge.start()
            self._web_server.set_ws_url(self._bridge.ws_url)
            self._web_server.start()
        except Exception as exc:
            self.stop()
            raise RuntimeError(f"Integracao com Strudel indisponivel: {exc}") from exc

        if self._config.auto_open_browser:
            webbrowser.open(self.web_url)

    def publish_state(self, motion: MotionFeatures, params: SoundParameters) -> None:
        if not self.enabled:
            return

        state = self._state_publisher.build_state(params, motion)
        if not state.active and not self._config.send_inactive_state:
            return

        if not self._state_publisher.should_publish(state):
            return

        self._bridge.publish(state.to_payload())

    def publish_preview(self, overlay) -> None:
        if not self.enabled:
            return

        if not self._preview_publisher.should_publish():
            return

        frame = self._preview_publisher.build_frame(overlay)
        self._bridge.publish(frame.to_payload())

    def stop(self) -> None:
        self._web_server.stop()
        self._bridge.stop()
