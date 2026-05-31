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
