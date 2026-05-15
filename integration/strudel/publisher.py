from __future__ import annotations

import time

from integration.strudel.code_generator import build_code
from integration.strudel.models import StrudelState
from integration.strudel.note_adapter import to_strudel_note
from utils.config import StrudelConfig
from utils.models import SoundParameters


class StrudelPublisher:
    def __init__(self, config: StrudelConfig) -> None:
        self._config = config
        self._last_state: StrudelState | None = None
        self._last_publish_at = 0.0

    def build_state(self, params: SoundParameters) -> StrudelState:
        active = params.active
        note_label = params.note_label if active else "--"
        strudel_note = to_strudel_note(note_label)
        gain = round(params.amplitude if active else 0.0, self._config.gain_precision)
        brightness = round(params.brightness if active else 0.0, 3)
        lpf = round(
            self._config.lpf_min
            + brightness * (self._config.lpf_max - self._config.lpf_min)
        )

        state = StrudelState(
            active=active,
            note_label=note_label,
            strudel_note=strudel_note,
            frequency=params.frequency if active else 0.0,
            gain=gain,
            brightness=brightness,
            lpf=lpf,
            synth=self._config.synth_name,
            code="",
            timestamp=time.time(),
        )
        state.code = build_code(state)
        return state

    def should_publish(self, state: StrudelState) -> bool:
        now = time.perf_counter()
        if self._last_state is None:
            self._remember(state, now)
            return True

        if state.active != self._last_state.active:
            self._remember(state, now)
            return True

        if (
            self._config.note_change_immediate
            and state.note_label != self._last_state.note_label
        ):
            self._remember(state, now)
            return True

        gain_delta = abs(state.gain - self._last_state.gain)
        brightness_delta = abs(state.brightness - self._last_state.brightness)
        elapsed = now - self._last_publish_at
        min_interval = 1.0 / max(self._config.update_hz, 1)

        if gain_delta >= self._config.gain_delta:
            self._remember(state, now)
            return True

        if brightness_delta >= self._config.brightness_delta:
            self._remember(state, now)
            return True

        if elapsed >= min_interval:
            self._remember(state, now)
            return True

        return False

    def _remember(self, state: StrudelState, now: float) -> None:
        self._last_state = state
        self._last_publish_at = now
