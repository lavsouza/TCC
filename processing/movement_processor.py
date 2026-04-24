from __future__ import annotations

from math import hypot

from utils.config import ProcessingConfig
from utils.models import HandFrame, MotionFeatures


class MovementProcessor:
    def __init__(self, config: ProcessingConfig) -> None:
        self._config = config
        self._prev_raw_x: float | None = None
        self._prev_raw_y: float | None = None
        self._prev_timestamp: float | None = None
        self._smoothed_x: float | None = None
        self._smoothed_y: float | None = None
        self._smoothed_velocity = 0.0
        self._smoothed_openness = 0.0

    def process(self, hand_frame: HandFrame | None) -> MotionFeatures:
        if hand_frame is None:
            self._prev_raw_x = None
            self._prev_raw_y = None
            self._prev_timestamp = None
            self._smoothed_x = None
            self._smoothed_y = None
            self._smoothed_velocity = 0.0
            self._smoothed_openness = 0.0
            return MotionFeatures()

        index_tip = hand_frame.landmarks[8]
        thumb_tip = hand_frame.landmarks[4]
        wrist = hand_frame.landmarks[0]
        middle_mcp = hand_frame.landmarks[9]

        raw_x = _clamp(index_tip.x)
        raw_y = _clamp(index_tip.y)
        raw_velocity = self._compute_velocity(raw_x, raw_y, hand_frame.timestamp)

        hand_scale = max(
            _distance(wrist.x, wrist.y, middle_mcp.x, middle_mcp.y),
            1e-4,
        )
        raw_openness = _clamp(
            _distance(thumb_tip.x, thumb_tip.y, index_tip.x, index_tip.y)
            / (hand_scale * self._config.hand_span_reference)
        )

        smoothed_x = _smooth(raw_x, self._smoothed_x, self._config.position_smoothing)
        smoothed_y = _smooth(raw_y, self._smoothed_y, self._config.position_smoothing)
        smoothed_velocity = _smooth(
            raw_velocity,
            self._smoothed_velocity,
            self._config.velocity_smoothing,
        )
        smoothed_openness = _smooth(
            raw_openness,
            self._smoothed_openness,
            self._config.openness_smoothing,
        )

        self._prev_raw_x = raw_x
        self._prev_raw_y = raw_y
        self._prev_timestamp = hand_frame.timestamp
        self._smoothed_x = smoothed_x
        self._smoothed_y = smoothed_y
        self._smoothed_velocity = smoothed_velocity
        self._smoothed_openness = smoothed_openness

        return MotionFeatures(
            raw_x=raw_x,
            raw_y=raw_y,
            x=smoothed_x,
            y=smoothed_y,
            velocity=smoothed_velocity,
            openness=smoothed_openness,
            active=True,
        )

    def _compute_velocity(self, raw_x: float, raw_y: float, timestamp: float) -> float:
        if (
            self._prev_timestamp is None
            or self._prev_raw_x is None
            or self._prev_raw_y is None
        ):
            return 0.0

        delta_t = max(timestamp - self._prev_timestamp, 1e-3)
        delta_pos = _distance(raw_x, raw_y, self._prev_raw_x, self._prev_raw_y)
        velocity = delta_pos / delta_t
        return _clamp(velocity / self._config.velocity_reference)


def _distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return hypot(x2 - x1, y2 - y1)


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def _smooth(value: float, previous: float | None, alpha: float) -> float:
    if previous is None:
        return value
    return previous + alpha * (value - previous)
