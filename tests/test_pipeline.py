from __future__ import annotations

import unittest

from mapping.gesture_mapper import GestureMapper
from processing.movement_processor import MovementProcessor
from utils.config import MappingConfig, ProcessingConfig
from utils.models import HandFrame, Landmark, MotionFeatures


def build_hand(
    *,
    index_x: float,
    index_y: float,
    thumb_x: float,
    thumb_y: float,
    timestamp: float,
) -> HandFrame:
    landmarks = [Landmark(x=0.5, y=0.5, z=0.0) for _ in range(21)]
    landmarks[0] = Landmark(x=0.45, y=0.82, z=0.0)
    landmarks[4] = Landmark(x=thumb_x, y=thumb_y, z=0.0)
    landmarks[8] = Landmark(x=index_x, y=index_y, z=0.0)
    landmarks[9] = Landmark(x=0.53, y=0.58, z=0.0)
    return HandFrame(landmarks=landmarks, handedness="right", timestamp=timestamp)


class MovementProcessorTests(unittest.TestCase):
    def test_processor_marks_frame_as_active_when_hand_exists(self) -> None:
        processor = MovementProcessor(ProcessingConfig())
        motion = processor.process(
            build_hand(
                index_x=0.4,
                index_y=0.5,
                thumb_x=0.35,
                thumb_y=0.55,
                timestamp=1.0,
            )
        )

        self.assertTrue(motion.active)
        self.assertGreaterEqual(motion.x, 0.0)
        self.assertLessEqual(motion.x, 1.0)

    def test_processor_extracts_velocity_from_consecutive_frames(self) -> None:
        processor = MovementProcessor(ProcessingConfig())
        processor.process(
            build_hand(
                index_x=0.3,
                index_y=0.5,
                thumb_x=0.28,
                thumb_y=0.57,
                timestamp=1.0,
            )
        )
        motion = processor.process(
            build_hand(
                index_x=0.6,
                index_y=0.35,
                thumb_x=0.4,
                thumb_y=0.48,
                timestamp=1.2,
            )
        )

        self.assertGreater(motion.velocity, 0.0)


class GestureMapperTests(unittest.TestCase):
    def test_mapper_increases_pitch_when_hand_moves_right(self) -> None:
        mapper = GestureMapper(MappingConfig())

        left = mapper.map(MotionFeatures(x=0.0, y=0.5, velocity=0.1, openness=0.2, active=True))
        right = mapper.map(MotionFeatures(x=1.0, y=0.5, velocity=0.1, openness=0.2, active=True))

        self.assertLess(left.frequency, right.frequency)

    def test_mapper_mutes_when_no_hand_is_detected(self) -> None:
        mapper = GestureMapper(MappingConfig())
        sound = mapper.map(MotionFeatures())

        self.assertFalse(sound.active)
        self.assertEqual(sound.amplitude, 0.0)


if __name__ == "__main__":
    unittest.main()
