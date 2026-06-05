from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class StrudelState:
    active: bool
    note_label: str
    strudel_note: str
    frequency: float
    gain: float
    brightness: float
    lpf: int
    synth: str
    hands_detected: int
    primary_handedness: str
    secondary_handedness: str
    brightness_source: str
    gesture_phase: str
    gesture_event: str
    gesture_label: str
    sweep_direction: str
    pattern_mode: str
    selected_preset: str
    preset_name: str
    preset_description: str
    preset_source: str
    emotion: str | None
    emotion_source: str | None
    preset_bpm: int
    preset_rhythm: str
    preset_default_synth: str
    preset_scale_notes: tuple[str, ...]
    preset_gain_scale: float
    preset_filter_offset: int
    preset_density: float
    code: str
    timestamp: float

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["type"] = "state"
        return payload


@dataclass(slots=True)
class PreviewFrame:
    image: str
    width: int
    height: int
    timestamp: float

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["type"] = "frame"
        return payload
