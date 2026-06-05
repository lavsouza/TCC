from __future__ import annotations

import time

from integration.strudel.code_generator import build_code
from integration.strudel.models import StrudelState
from integration.strudel.note_adapter import to_strudel_note
from integration.strudel.presets import default_preset, get_preset
from utils.config import StrudelConfig
from utils.models import MotionFeatures, SoundParameters


class StrudelPublisher:
    def __init__(self, config: StrudelConfig) -> None:
        self._config = config
        self._selected_preset_id = default_preset().id
        self._last_state: StrudelState | None = None
        self._last_publish_at = 0.0

    def set_selected_preset(self, preset_id: str | None) -> None:
        self._selected_preset_id = get_preset(preset_id).id

    def get_selected_preset(self) -> str:
        return self._selected_preset_id

    def build_state(
        self,
        params: SoundParameters,
        motion: MotionFeatures | None = None,
    ) -> StrudelState:
        preset = get_preset(self._selected_preset_id)
        active = params.active
        note_label = params.note_label if active else "--"
        strudel_note = to_strudel_note(note_label)
        gain = round(
            (params.amplitude if active else 0.0) * preset.gain_scale,
            self._config.gain_precision,
        )
        brightness = round(params.brightness if active else 0.0, 3)
        base_lpf = round(
            self._config.lpf_min
            + brightness * (self._config.lpf_max - self._config.lpf_min)
        )
        hands_detected = motion.hands_detected if motion is not None else 0
        primary_handedness = motion.handedness if motion is not None and motion.active else "none"
        secondary_handedness = (
            motion.secondary_handedness if motion is not None and motion.has_secondary else "none"
        )
        brightness_source = (
            secondary_handedness
            if secondary_handedness != "none"
            else primary_handedness
        )
        lpf = max(
            self._config.lpf_min,
            min(self._config.lpf_max + 1200, base_lpf + preset.filter_offset),
        )
        effective_synth = (
            params.synth_name
            if active and secondary_handedness != "none"
            else preset.default_synth
        )

        state = StrudelState(
            active=active,
            note_label=note_label,
            strudel_note=strudel_note,
            frequency=params.frequency if active else 0.0,
            gain=gain,
            brightness=brightness,
            lpf=lpf,
            synth=effective_synth if active else preset.default_synth,
            hands_detected=hands_detected,
            primary_handedness=primary_handedness,
            secondary_handedness=secondary_handedness,
            brightness_source=brightness_source,
            gesture_phase=params.gesture_phase,
            gesture_event=params.gesture_event,
            gesture_label=params.gesture_label,
            sweep_direction=params.sweep_direction,
            pattern_mode=params.pattern_mode,
            selected_preset=preset.id,
            preset_name=preset.name,
            preset_description=preset.description,
            preset_source="manual",
            emotion=None,
            emotion_source=None,
            preset_bpm=preset.bpm,
            preset_rhythm=preset.rhythm_pattern,
            preset_default_synth=preset.default_synth,
            preset_scale_notes=preset.scale_notes,
            preset_gain_scale=preset.gain_scale,
            preset_filter_offset=preset.filter_offset,
            preset_density=preset.density,
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

        if state.synth != self._last_state.synth:
            self._remember(state, now)
            return True

        if state.hands_detected != self._last_state.hands_detected:
            self._remember(state, now)
            return True

        if state.primary_handedness != self._last_state.primary_handedness:
            self._remember(state, now)
            return True

        if state.secondary_handedness != self._last_state.secondary_handedness:
            self._remember(state, now)
            return True

        if state.gesture_phase != self._last_state.gesture_phase:
            self._remember(state, now)
            return True

        if state.gesture_event != self._last_state.gesture_event:
            self._remember(state, now)
            return True

        if state.pattern_mode != self._last_state.pattern_mode:
            self._remember(state, now)
            return True

        if state.selected_preset != self._last_state.selected_preset:
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
