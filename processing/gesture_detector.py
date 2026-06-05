from __future__ import annotations

from dataclasses import dataclass

from utils.config import ProcessingConfig
from utils.models import GestureState, HandMotion


@dataclass(slots=True)
class _PrimaryGestureTracker:
    is_pinched: bool = False
    pinch_started_at: float | None = None
    hold_emitted: bool = False
    last_x: float | None = None
    last_y: float | None = None
    last_timestamp: float | None = None
    last_sweep_at: float = 0.0


class PrimaryGestureDetector:
    def __init__(self, config: ProcessingConfig) -> None:
        self._config = config
        self._trackers: dict[str, _PrimaryGestureTracker] = {}

    def update(self, motion: HandMotion) -> GestureState:
        if not motion.active:
            return GestureState()

        tracker = self._trackers.setdefault(motion.handedness, _PrimaryGestureTracker())
        event = "none"
        phase = "idle"
        sweep_direction = "none"
        timestamp = motion.timestamp

        should_close_pinch = motion.openness <= self._config.pinch_close_threshold
        should_open_pinch = motion.openness >= self._config.pinch_open_threshold

        if not tracker.is_pinched and should_close_pinch:
            tracker.is_pinched = True
            tracker.pinch_started_at = timestamp
            tracker.hold_emitted = False
            event = "pinch"
        elif tracker.is_pinched and should_open_pinch:
            tracker.is_pinched = False
            tracker.pinch_started_at = None
            tracker.hold_emitted = False
            event = "release"

        if tracker.is_pinched:
            if (
                tracker.pinch_started_at is not None
                and not tracker.hold_emitted
                and (timestamp - tracker.pinch_started_at) >= self._config.hold_min_duration
            ):
                tracker.hold_emitted = True
                event = "hold"

            phase = "hold" if tracker.hold_emitted else "pinch"
        else:
            phase = "idle"

        if event == "none" and self._is_sweep_candidate(tracker, motion):
            sweep_direction = "right" if motion.x > (tracker.last_x or 0.0) else "left"
            event = "sweep"
            tracker.last_sweep_at = timestamp

        tracker.last_x = motion.x
        tracker.last_y = motion.y
        tracker.last_timestamp = timestamp

        return GestureState(
            phase=phase,
            event=event,
            sweep_direction=sweep_direction,
            timestamp=timestamp,
        )

    def discard_missing(self, active_handedness: set[str]) -> None:
        for handedness in tuple(self._trackers):
            if handedness not in active_handedness:
                del self._trackers[handedness]

    def reset(self) -> None:
        self._trackers.clear()

    def _is_sweep_candidate(
        self,
        tracker: _PrimaryGestureTracker,
        motion: HandMotion,
    ) -> bool:
        if tracker.last_x is None or tracker.last_y is None or tracker.last_timestamp is None:
            return False

        if (motion.timestamp - tracker.last_sweep_at) < self._config.sweep_cooldown:
            return False

        delta_x = motion.x - tracker.last_x
        delta_y = motion.y - tracker.last_y

        return (
            motion.velocity >= self._config.sweep_velocity_threshold
            and abs(delta_x) >= self._config.sweep_delta_x_threshold
            and abs(delta_y) <= self._config.sweep_max_delta_y
        )
