from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Landmark:
    x: float
    y: float
    z: float = 0.0


@dataclass(slots=True)
class HandFrame:
    landmarks: list[Landmark]
    handedness: str
    timestamp: float


@dataclass(slots=True)
class MotionFeatures:
    raw_x: float = 0.0
    raw_y: float = 0.0
    x: float = 0.0
    y: float = 0.0
    velocity: float = 0.0
    openness: float = 0.0
    active: bool = False


@dataclass(slots=True, frozen=True)
class ScaleNote:
    midi: int
    label: str
    frequency: float


@dataclass(slots=True)
class SoundParameters:
    frequency: float = 220.0
    amplitude: float = 0.0
    brightness: float = 0.0
    note_label: str = "--"
    active: bool = False
