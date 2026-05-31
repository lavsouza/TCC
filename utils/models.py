from __future__ import annotations

from dataclasses import dataclass, field


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

    @property
    def anchor_x(self) -> float:
        if not self.landmarks:
            return 0.0
        return self.landmarks[0].x


@dataclass(slots=True)
class HandsFrame:
    hands: list[HandFrame]
    timestamp: float

    @property
    def count(self) -> int:
        return len(self.hands)

    @property
    def handedness_labels(self) -> tuple[str, ...]:
        return tuple(hand.handedness for hand in self.hands)

    def get_hand(self, handedness: str) -> HandFrame | None:
        for hand in self.hands:
            if hand.handedness == handedness:
                return hand
        return None

    def select_primary(self, preferred_handedness: str | None = None) -> HandFrame | None:
        if preferred_handedness:
            hand = self.get_hand(preferred_handedness.lower())
            if hand is not None:
                return hand

        for fallback in ("right", "left"):
            hand = self.get_hand(fallback)
            if hand is not None:
                return hand

        if not self.hands:
            return None
        return self.hands[0]

    def select_secondary(self, primary_handedness: str | None = None) -> HandFrame | None:
        if len(self.hands) < 2:
            return None

        if primary_handedness:
            normalized = primary_handedness.lower()
            for hand in self.hands:
                if hand.handedness != normalized:
                    return hand

        return self.hands[1]


@dataclass(slots=True)
class HandMotion:
    raw_x: float = 0.0
    raw_y: float = 0.0
    x: float = 0.0
    y: float = 0.0
    velocity: float = 0.0
    openness: float = 0.0
    handedness: str = "none"
    active: bool = False


@dataclass(slots=True)
class MotionFeatures:
    primary: HandMotion = field(default_factory=HandMotion)
    secondary: HandMotion = field(default_factory=HandMotion)
    hands_detected: int = 0

    @property
    def active(self) -> bool:
        return self.primary.active

    @property
    def raw_x(self) -> float:
        return self.primary.raw_x

    @property
    def raw_y(self) -> float:
        return self.primary.raw_y

    @property
    def x(self) -> float:
        return self.primary.x

    @property
    def y(self) -> float:
        return self.primary.y

    @property
    def velocity(self) -> float:
        return self.primary.velocity

    @property
    def openness(self) -> float:
        return self.primary.openness

    @property
    def handedness(self) -> str:
        return self.primary.handedness

    @property
    def has_secondary(self) -> bool:
        return self.secondary.active

    @property
    def secondary_handedness(self) -> str:
        return self.secondary.handedness


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
    synth_name: str = "sawtooth"
    active: bool = False
