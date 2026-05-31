from __future__ import annotations

import unittest

from mapping.gesture_mapper import GestureMapper
from processing.movement_processor import MovementProcessor
from utils.config import MappingConfig, ProcessingConfig
from utils.models import HandFrame, HandMotion, HandsFrame, Landmark, MotionFeatures


def build_hand(
    *,
    index_x: float,
    index_y: float,
    thumb_x: float,
    thumb_y: float,
    timestamp: float,
    handedness: str = "right",
) -> HandFrame:
    landmarks = [Landmark(x=0.5, y=0.5, z=0.0) for _ in range(21)]
    landmarks[0] = Landmark(x=0.45, y=0.82, z=0.0)
    landmarks[4] = Landmark(x=thumb_x, y=thumb_y, z=0.0)
    landmarks[8] = Landmark(x=index_x, y=index_y, z=0.0)
    landmarks[9] = Landmark(x=0.53, y=0.58, z=0.0)
    return HandFrame(landmarks=landmarks, handedness=handedness, timestamp=timestamp)


def build_hands_frame(*hands: HandFrame, timestamp: float) -> HandsFrame:
    return HandsFrame(hands=list(hands), timestamp=timestamp)


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

    def test_processor_selects_preferred_handedness_when_two_hands_exist(self) -> None:
        processor = MovementProcessor(ProcessingConfig(primary_handedness="left"))
        right_hand = build_hand(
            index_x=0.35,
            index_y=0.45,
            thumb_x=0.30,
            thumb_y=0.50,
            timestamp=1.0,
        )
        left_hand = build_hand(
            index_x=0.72,
            index_y=0.40,
            thumb_x=0.66,
            thumb_y=0.52,
            timestamp=1.0,
            handedness="left",
        )
        left_hand.landmarks[0] = Landmark(x=0.62, y=0.80, z=0.0)
        left_hand.landmarks[9] = Landmark(x=0.58, y=0.58, z=0.0)

        motion = processor.process(build_hands_frame(right_hand, left_hand, timestamp=1.0))

        self.assertTrue(motion.active)
        self.assertEqual(motion.handedness, "left")
        self.assertAlmostEqual(motion.x, 0.72)

    def test_processor_falls_back_to_other_hand_when_preferred_is_missing(self) -> None:
        processor = MovementProcessor(ProcessingConfig(primary_handedness="right"))
        left_hand = build_hand(
            index_x=0.72,
            index_y=0.40,
            thumb_x=0.66,
            thumb_y=0.52,
            timestamp=1.0,
            handedness="left",
        )
        left_hand.landmarks[0] = Landmark(x=0.62, y=0.80, z=0.0)
        left_hand.landmarks[9] = Landmark(x=0.58, y=0.58, z=0.0)

        motion = processor.process(build_hands_frame(left_hand, timestamp=1.0))

        self.assertTrue(motion.active)
        self.assertEqual(motion.handedness, "left")
        self.assertAlmostEqual(motion.x, 0.72)

    def test_processor_exposes_secondary_hand_motion_when_two_hands_exist(self) -> None:
        processor = MovementProcessor(ProcessingConfig(primary_handedness="right"))
        right_hand = build_hand(
            index_x=0.35,
            index_y=0.45,
            thumb_x=0.30,
            thumb_y=0.50,
            timestamp=1.0,
            handedness="right",
        )
        left_hand = build_hand(
            index_x=0.68,
            index_y=0.32,
            thumb_x=0.60,
            thumb_y=0.42,
            timestamp=1.0,
            handedness="left",
        )
        left_hand.landmarks[0] = Landmark(x=0.62, y=0.80, z=0.0)
        left_hand.landmarks[9] = Landmark(x=0.58, y=0.58, z=0.0)

        motion = processor.process(build_hands_frame(right_hand, left_hand, timestamp=1.0))

        self.assertTrue(motion.active)
        self.assertTrue(motion.has_secondary)
        self.assertEqual(motion.handedness, "right")
        self.assertEqual(motion.secondary_handedness, "left")
        self.assertAlmostEqual(motion.secondary.x, 0.68)


class GestureMapperTests(unittest.TestCase):
    def test_mapper_increases_pitch_when_hand_moves_right(self) -> None:
        mapper = GestureMapper(MappingConfig())

        left = mapper.map(
            MotionFeatures(
                primary=HandMotion(x=0.0, y=0.5, velocity=0.1, openness=0.2, active=True),
                hands_detected=1,
            )
        )
        right = mapper.map(
            MotionFeatures(
                primary=HandMotion(x=1.0, y=0.5, velocity=0.1, openness=0.2, active=True),
                hands_detected=1,
            )
        )

        self.assertLess(left.frequency, right.frequency)

    def test_mapper_mutes_when_no_hand_is_detected(self) -> None:
        mapper = GestureMapper(MappingConfig())
        sound = mapper.map(MotionFeatures())

        self.assertFalse(sound.active)
        self.assertEqual(sound.amplitude, 0.0)

    def test_mapper_uses_secondary_hand_for_brightness_and_synth(self) -> None:
        mapper = GestureMapper(MappingConfig())
        motion = MotionFeatures(
            primary=HandMotion(
                x=0.35,
                y=0.25,
                velocity=0.1,
                openness=0.15,
                handedness="right",
                active=True,
            ),
            secondary=HandMotion(
                x=0.98,
                y=0.45,
                velocity=0.5,
                openness=0.8,
                handedness="left",
                active=True,
            ),
            hands_detected=2,
        )

        sound = mapper.map(motion)

        self.assertEqual(sound.synth_name, "square")
        self.assertGreater(sound.brightness, 0.5)


if __name__ == "__main__":
    unittest.main()
