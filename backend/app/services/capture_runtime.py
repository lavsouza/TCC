from __future__ import annotations

import time
from threading import Event, Lock, Thread

from backend.app.contracts.events import make_event
from backend.app.services.realtime_hub import RealtimeHub
from backend.app.services.state_service import StateService
from capture.hand_tracker import HandTracker
from utils.config import CameraConfig


class CaptureRuntime:
    """Executa camera/MediaPipe em thread propria e publica eventos versionados."""

    def __init__(
        self,
        camera_config: CameraConfig,
        state_service: StateService,
        hub: RealtimeHub,
    ) -> None:
        self._camera_config = camera_config
        self._state_service = state_service
        self._hub = hub
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._status_lock = Lock()
        self._running = False
        self._last_error: str | None = None
        self._frames_processed = 0

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="movecodebeats-capture",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        self._thread = None

    def status(self) -> dict[str, object]:
        with self._status_lock:
            return {
                "enabled": True,
                "running": self._running,
                "last_error": self._last_error,
                "frames_processed": self._frames_processed,
            }

    def _run(self) -> None:
        tracker: HandTracker | None = None
        try:
            tracker = HandTracker(self._camera_config)
            self._set_status(running=True, error=None)
            self._publish_runtime_status("running")

            while not self._stop_event.is_set():
                frame, hands_frame = tracker.read()
                events = self._state_service.process_frame(frame, hands_frame)
                with self._status_lock:
                    self._frames_processed += 1
                for event_type, data in events:
                    self._hub.publish_from_capture(make_event(event_type, data))
        except Exception as exc:
            self._set_status(running=False, error=str(exc))
            self._publish_runtime_status("error")
        finally:
            if tracker is not None:
                tracker.close()
            self._set_status(running=False)
            self._publish_runtime_status("stopped")

    def _set_status(
        self,
        *,
        running: bool,
        error: str | None = None,
    ) -> None:
        with self._status_lock:
            self._running = running
            if error is not None or running:
                self._last_error = error

    def _publish_runtime_status(self, status: str) -> None:
        self._hub.publish_from_capture(
            make_event(
                "runtime.status.v1",
                {
                    "status": status,
                    "capture": self.status(),
                    "timestamp": time.time(),
                },
            )
        )
