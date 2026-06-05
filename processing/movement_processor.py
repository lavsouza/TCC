from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from processing.gesture_detector import PrimaryGestureDetector
from utils.config import ProcessingConfig
from utils.models import HandFrame, HandMotion, HandsFrame, MotionFeatures


@dataclass(slots=True)
class _TrackedHandState:
    prev_raw_x: float | None = None
    prev_raw_y: float | None = None
    prev_timestamp: float | None = None
    smoothed_x: float | None = None
    smoothed_y: float | None = None
    smoothed_velocity: float = 0.0
    smoothed_openness: float = 0.0


class MovementProcessor:
    def __init__(self, config: ProcessingConfig) -> None:
        self._config = config
        self._hand_states: dict[str, _TrackedHandState] = {}
        self._gesture_detector = PrimaryGestureDetector(config)
        self._active_handedness: str | None = None

    def process(self, hand_frame: HandFrame | HandsFrame | None) -> MotionFeatures:
        hands = _normalize_hands(hand_frame)
        if not hands:
            self._reset()
            return MotionFeatures()

        active_handedness = {hand.handedness for hand in hands}
        self._drop_stale_states(active_handedness)
        self._gesture_detector.discard_missing(active_handedness)

        primary_hand = self._select_primary(hand_frame)
        if primary_hand is None:
            self._reset()
            return MotionFeatures(hands_detected=len(hands))

        secondary_hand = self._select_secondary(hand_frame, primary_hand)
        primary_motion = self._build_hand_motion(primary_hand)
        secondary_motion = (
            self._build_hand_motion(secondary_hand)
            if secondary_hand is not None
            else HandMotion()
        )
        gesture = self._gesture_detector.update(primary_motion)

        self._active_handedness = primary_hand.handedness
        return MotionFeatures(
            primary=primary_motion,
            secondary=secondary_motion,
            gesture=gesture,
            hands_detected=len(hands),
        )

    def _select_primary(self, hand_frame: HandFrame | HandsFrame | None) -> HandFrame | None:
        if hand_frame is None:
            return None

        if isinstance(hand_frame, HandFrame):
            return hand_frame

        preferred = self._active_handedness or self._config.primary_handedness
        return hand_frame.select_primary(preferred)

    def _select_secondary(
        self,
        hand_frame: HandFrame | HandsFrame | None,
        primary_hand: HandFrame,
    ) -> HandFrame | None:
        if hand_frame is None or isinstance(hand_frame, HandFrame):
            return None

        return hand_frame.select_secondary(primary_hand.handedness)

    def _build_hand_motion(self, hand: HandFrame) -> HandMotion:
        state = self._hand_states.setdefault(hand.handedness, _TrackedHandState())

        index_tip = hand.landmarks[8]
        thumb_tip = hand.landmarks[4]
        wrist = hand.landmarks[0]
        middle_mcp = hand.landmarks[9]

        raw_x = _clamp(index_tip.x)
        raw_y = _clamp(index_tip.y)
        raw_velocity = self._compute_velocity(state, raw_x, raw_y, hand.timestamp)

        hand_scale = max(
            _distance(wrist.x, wrist.y, middle_mcp.x, middle_mcp.y),
            1e-4,
        )
        raw_openness = _clamp(
            _distance(thumb_tip.x, thumb_tip.y, index_tip.x, index_tip.y)
            / (hand_scale * self._config.hand_span_reference)
        )

        smoothed_x = _smooth(raw_x, state.smoothed_x, self._config.position_smoothing)
        smoothed_y = _smooth(raw_y, state.smoothed_y, self._config.position_smoothing)
        smoothed_velocity = _smooth(
            raw_velocity,
            state.smoothed_velocity,
            self._config.velocity_smoothing,
        )
        smoothed_openness = _smooth(
            raw_openness,
            state.smoothed_openness,
            self._config.openness_smoothing,
        )

        state.prev_raw_x = raw_x
        state.prev_raw_y = raw_y
        state.prev_timestamp = hand.timestamp
        state.smoothed_x = smoothed_x
        state.smoothed_y = smoothed_y
        state.smoothed_velocity = smoothed_velocity
        state.smoothed_openness = smoothed_openness

        return HandMotion(
            raw_x=raw_x,
            raw_y=raw_y,
            x=smoothed_x,
            y=smoothed_y,
            velocity=smoothed_velocity,
            openness=smoothed_openness,
            handedness=hand.handedness,
            timestamp=hand.timestamp,
            active=True,
        )

    def _drop_stale_states(self, active_handedness: set[str]) -> None:
        for handedness in tuple(self._hand_states):
            if handedness not in active_handedness:
                del self._hand_states[handedness]

        if self._active_handedness not in active_handedness:
            self._active_handedness = None

    def _reset(self) -> None:
        self._hand_states.clear()
        self._gesture_detector.reset()
        self._active_handedness = None

    def _compute_velocity(
        self,
        state: _TrackedHandState,
        raw_x: float,
        raw_y: float,
        timestamp: float,
    ) -> float:
        if (
            state.prev_timestamp is None
            or state.prev_raw_x is None
            or state.prev_raw_y is None
        ):
            return 0.0

        delta_t = max(timestamp - state.prev_timestamp, 1e-3)
        delta_pos = _distance(raw_x, raw_y, state.prev_raw_x, state.prev_raw_y)
        velocity = delta_pos / delta_t
        return _clamp(velocity / self._config.velocity_reference)


def _normalize_hands(hand_frame: HandFrame | HandsFrame | None) -> list[HandFrame]:
    if hand_frame is None:
        return []

    if isinstance(hand_frame, HandFrame):
        return [hand_frame]

    return hand_frame.hands


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return hypot(x2 - x1, y2 - y1)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _smooth(value: float, previous: float | None, alpha: float) -> float:
    if previous is None:
        return value
    return previous + alpha * (value - previous)
