from __future__ import annotations

import time
from integration.strudel.models import StrudelState
from integration.strudel.note_adapter import to_strudel_note
from integration.strudel.presets import (
    get_default_emotion_profile,
    get_emotion_profile,
    select_rhythm_pattern,
)
from integration.strudel.scenes import get_scene, resolve_scene_payload
from utils.config import StrudelConfig
from utils.models import MotionFeatures, SoundParameters


class StrudelPublisher:
    def __init__(self, config: StrudelConfig) -> None:
        self._config = config
        self._selected_profile_id = get_default_emotion_profile().id
        self._emotion_source = "manual"
        self._emotion_confidence = 1.0
        self._last_state: StrudelState | None = None
        self._last_publish_at = 0.0

    def set_selected_profile(
        self,
        profile_id: str | None,
        *,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> None:
        self._selected_profile_id = get_emotion_profile(profile_id).id
        self._emotion_source = source
        self._emotion_confidence = _clamp(confidence, 0.0, 1.0)

    def get_selected_profile(self) -> str:
        return self._selected_profile_id

    def set_selected_preset(self, preset_id: str | None) -> None:
        self.set_selected_profile(preset_id)

    def get_selected_preset(self) -> str:
        return self.get_selected_profile()

    def build_state(
        self,
        params: SoundParameters,
        motion: MotionFeatures | None = None,
    ) -> StrudelState:
        profile = get_emotion_profile(self._selected_profile_id)
        active = params.active
        note_label = params.note_label if active else "--"
        strudel_note = to_strudel_note(note_label)
        gain = 0.0
        if active:
            gain = round(
                _clamp(
                    params.amplitude * profile.intensity,
                    profile.gain_range[0],
                    profile.gain_range[1],
                ),
                self._config.gain_precision,
            )
        brightness = round(params.brightness if active else 0.0, 3)
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
        lpf = round(
            profile.lpf_range[0]
            + brightness * (profile.lpf_range[1] - profile.lpf_range[0])
        )
        effective_synth = (
            params.synth_name
            if active and secondary_handedness != "none"
            else profile.default_synth
        )
        rhythm_pattern = select_rhythm_pattern(profile, params.pattern_mode)
        scene = resolve_scene_payload(get_scene(profile.id), params.pattern_mode)
        scene_layers = tuple(layer["id"] for layer in scene["layers"])

        state = StrudelState(
            active=active,
            note_label=note_label,
            strudel_note=strudel_note,
            frequency=params.frequency if active else 0.0,
            gain=gain,
            brightness=brightness,
            lpf=lpf,
            synth=effective_synth if active else profile.default_synth,
            hands_detected=hands_detected,
            primary_handedness=primary_handedness,
            secondary_handedness=secondary_handedness,
            brightness_source=brightness_source,
            gesture_phase=params.gesture_phase,
            gesture_event=params.gesture_event,
            gesture_label=params.gesture_label,
            sweep_direction=params.sweep_direction,
            pattern_mode=params.pattern_mode,
            emotion=profile.emotion,
            emotion_label=profile.label,
            emotion_source=self._emotion_source,
            emotion_confidence=self._emotion_confidence,
            selected_profile=profile.id,
            profile_name=profile.label,
            profile_description=profile.description,
            profile_bpm=profile.bpm,
            profile_density=profile.density,
            profile_intensity=profile.intensity,
            profile_variation=profile.variation,
            profile_gain_range=profile.gain_range,
            profile_lpf_range=profile.lpf_range,
            profile_synth_family=profile.synth_family,
            profile_scale_notes=profile.scale_notes,
            profile_rhythm_patterns=profile.rhythm_patterns,
            profile_rhythm=rhythm_pattern,
            profile_transition_seconds=profile.transition_seconds,
            scene=scene,
            scene_name=str(scene["name"]),
            scene_description=str(scene["description"]),
            scene_layers=scene_layers,
            scene_beats_per_cycle=int(scene["beats_per_cycle"]),
            selected_preset=profile.id,
            preset_name=profile.label,
            preset_description=profile.description,
            preset_source=self._emotion_source,
            preset_bpm=profile.bpm,
            preset_rhythm=rhythm_pattern,
            preset_default_synth=profile.default_synth,
            preset_scale_notes=profile.scale_notes,
            preset_gain_scale=profile.gain_scale,
            preset_filter_offset=profile.filter_offset,
            preset_density=profile.density,
            code="",
            timestamp=time.time(),
        )
        return state

    def should_publish(self, state: StrudelState) -> bool:
        now = time.perf_counter()
        if self._last_state is None:
            self._remember(state, now)
            return True

        if self._has_immediate_change(state):
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

    def _has_immediate_change(self, state: StrudelState) -> bool:
        previous = self._last_state
        if previous is None:
            return True

        note_changed = (
            self._config.note_change_immediate
            and state.note_label != previous.note_label
        )
        structural_state = (
            state.active,
            state.synth,
            state.hands_detected,
            state.primary_handedness,
            state.secondary_handedness,
            state.gesture_phase,
            state.gesture_event,
            state.pattern_mode,
            state.selected_profile,
        )
        previous_structural_state = (
            previous.active,
            previous.synth,
            previous.hands_detected,
            previous.primary_handedness,
            previous.secondary_handedness,
            previous.gesture_phase,
            previous.gesture_event,
            previous.pattern_mode,
            previous.selected_profile,
        )
        return note_changed or structural_state != previous_structural_state


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
