from __future__ import annotations

from threading import RLock

from integration.strudel.presets import (
    get_default_emotion_profile,
    get_emotion_profile,
    is_known_emotion_id,
    list_emotion_profiles,
)
from integration.strudel.preview_publisher import PreviewPublisher
from integration.strudel.publisher import StrudelPublisher
from mapping.gesture_mapper import GestureMapper
from processing.movement_processor import MovementProcessor
from utils.config import AppConfig
from utils.visualizer import render_overlay


class StateService:
    """Transforma frames detectados em estado musical, sem conhecer HTTP."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._processor = MovementProcessor(config.processing)
        self._mapper = GestureMapper(config.mapping)
        self._publisher = StrudelPublisher(config.strudel)
        self._preview = PreviewPublisher(config.strudel)
        self._lock = RLock()

    def process_frame(self, frame, hands_frame) -> list[tuple[str, dict[str, object]]]:
        with self._lock:
            motion = self._processor.process(hands_frame)
            params = self._mapper.map(motion)
            events: list[tuple[str, dict[str, object]]] = []

            state = self._publisher.build_state(params, motion)
            if (
                state.active or self._config.strudel.send_inactive_state
            ) and self._publisher.should_publish(state):
                payload = state.to_payload()
                payload.pop("type", None)
                events.append(("music.state.v1", payload))

            if self._preview.should_publish():
                overlay = render_overlay(frame, hands_frame, motion)
                preview = self._preview.build_frame(overlay).to_payload()
                preview.pop("type", None)
                events.append(("preview.frame.v1", preview))

            return events

    def select_profile(
        self,
        profile_id: str,
        *,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> dict[str, object]:
        if not is_known_emotion_id(profile_id):
            raise ValueError(f"Perfil desconhecido: {profile_id}")

        with self._lock:
            self._publisher.set_selected_profile(
                profile_id,
                source=source,
                confidence=confidence,
            )
            return get_emotion_profile(profile_id).to_payload()

    def selected_profile_id(self) -> str:
        with self._lock:
            return self._publisher.get_selected_profile()

    @staticmethod
    def catalog() -> list[dict[str, object]]:
        return [profile.to_payload() for profile in list_emotion_profiles()]

    @staticmethod
    def default_profile_id() -> str:
        return get_default_emotion_profile().id

    @staticmethod
    def get_profile(profile_id: str) -> dict[str, object]:
        if not is_known_emotion_id(profile_id):
            raise ValueError(f"Perfil desconhecido: {profile_id}")
        return get_emotion_profile(profile_id).to_payload()
