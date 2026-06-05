from __future__ import annotations

from pathlib import Path
import socket
import time
import unittest

from integration.strudel.bridge_server import StrudelBridgeServer
from integration.strudel.note_adapter import to_strudel_note
from integration.strudel.preview_publisher import PreviewPublisher
from integration.strudel.presets import default_preset, get_preset, list_presets
from integration.strudel.publisher import StrudelPublisher
from integration.strudel.web_server import StrudelWebServer
import numpy as np
from utils.config import PROJECT_ROOT, StrudelConfig
from utils.models import HandMotion, MotionFeatures, SoundParameters


class NoteAdapterTests(unittest.TestCase):
    def test_converts_sharp_note_labels_to_strudel_tokens(self) -> None:
        self.assertEqual(to_strudel_note("A#4"), "a#4")
        self.assertEqual(to_strudel_note("C3"), "c3")

    def test_returns_rest_token_for_inactive_labels(self) -> None:
        self.assertEqual(to_strudel_note("--"), "~")
        self.assertEqual(to_strudel_note("~"), "~")


class PresetCatalogTests(unittest.TestCase):
    def test_expected_presets_exist(self) -> None:
        preset_ids = {preset.id for preset in list_presets()}

        self.assertIn("neutral", preset_ids)
        self.assertIn("happy", preset_ids)
        self.assertIn("sad", preset_ids)
        self.assertIn("angry", preset_ids)

    def test_unknown_preset_falls_back_to_neutral(self) -> None:
        self.assertEqual(get_preset("unknown").id, "neutral")
        self.assertEqual(get_preset(None).id, "neutral")
        self.assertEqual(default_preset().id, "neutral")
        self.assertEqual(get_preset("andry").id, "angry")


class StrudelPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = StrudelConfig(
            enabled=True,
            update_hz=8,
            gain_delta=0.03,
            brightness_delta=0.05,
            lpf_min=400,
            lpf_max=4000,
            synth_name="triangle",
        )
        self.publisher = StrudelPublisher(self.config)

    def test_build_state_generates_expected_code_and_filter(self) -> None:
        self.publisher.set_selected_preset("happy")
        params = SoundParameters(
            frequency=466.2,
            amplitude=0.35,
            brightness=0.20,
            note_label="A#4",
            synth_name="square",
            gesture_phase="pinch",
            gesture_event="pinch",
            gesture_label="pinch",
            pattern_mode="pulse",
            active=True,
        )
        motion = MotionFeatures(
            primary=HandMotion(handedness="right", active=True),
            secondary=HandMotion(handedness="left", active=True),
            hands_detected=2,
        )

        state = self.publisher.build_state(params, motion)

        self.assertTrue(state.active)
        self.assertEqual(state.note_label, "A#4")
        self.assertEqual(state.strudel_note, "a#4")
        self.assertEqual(state.gain, 0.378)
        self.assertEqual(state.lpf, 1670)
        self.assertEqual(state.synth, "square")
        self.assertEqual(state.primary_handedness, "right")
        self.assertEqual(state.secondary_handedness, "left")
        self.assertEqual(state.brightness_source, "left")
        self.assertEqual(state.gesture_phase, "pinch")
        self.assertEqual(state.gesture_event, "pinch")
        self.assertEqual(state.gesture_label, "pinch")
        self.assertEqual(state.pattern_mode, "pulse")
        self.assertEqual(state.selected_preset, "happy")
        self.assertEqual(state.preset_name, "Happy")
        self.assertEqual(state.preset_source, "manual")
        self.assertIsNone(state.emotion)
        self.assertIsNone(state.emotion_source)
        self.assertEqual(
            state.code,
            '((note("a#4 a#4 ~ a#4").s("square").gain(0.378).lpf(1670).fast(1.539)).fast(1.35)).gain(0.461).lpf(2120)',
        )

    def test_state_payload_includes_gesture_fields(self) -> None:
        self.publisher.set_selected_preset("sad")
        params = SoundParameters(
            frequency=261.6,
            amplitude=0.25,
            brightness=0.10,
            note_label="C4",
            synth_name="triangle",
            gesture_phase="hold",
            gesture_event="hold",
            gesture_label="hold",
            pattern_mode="stutter",
            active=True,
        )
        motion = MotionFeatures(
            primary=HandMotion(handedness="right", active=True),
            hands_detected=1,
        )

        payload = self.publisher.build_state(params, motion).to_payload()

        self.assertEqual(payload["gesture_phase"], "hold")
        self.assertEqual(payload["gesture_event"], "hold")
        self.assertEqual(payload["gesture_label"], "hold")
        self.assertEqual(payload["pattern_mode"], "stutter")
        self.assertEqual(payload["selected_preset"], "sad")
        self.assertEqual(payload["preset_name"], "Sad")
        self.assertEqual(payload["preset_source"], "manual")
        self.assertIsNone(payload["emotion"])
        self.assertIsNone(payload["emotion_source"])

    def test_build_state_turns_inactive_params_into_hush_code(self) -> None:
        params = SoundParameters(
            frequency=0.0,
            amplitude=0.0,
            brightness=0.0,
            note_label="--",
            active=False,
        )

        state = self.publisher.build_state(params, MotionFeatures())

        self.assertFalse(state.active)
        self.assertEqual(state.strudel_note, "~")
        self.assertEqual(state.code, "hush()")

    def test_state_uses_neutral_preset_when_none_was_selected(self) -> None:
        state = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.2,
                brightness=0.1,
                note_label="C4",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )

        self.assertEqual(state.selected_preset, "neutral")
        self.assertEqual(state.preset_name, "Neutral")

    def test_should_publish_immediately_on_first_state_and_note_change(self) -> None:
        first = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )
        second = self.publisher.build_state(
            SoundParameters(
                frequency=293.7,
                amplitude=0.25,
                brightness=0.10,
                note_label="D4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )

        self.assertTrue(self.publisher.should_publish(first))
        self.assertTrue(self.publisher.should_publish(second))

    def test_should_wait_for_interval_when_state_change_is_below_threshold(self) -> None:
        first = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )
        subtle = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.26,
                brightness=0.12,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )

        self.assertTrue(self.publisher.should_publish(first))
        self.assertFalse(self.publisher.should_publish(subtle))

        time.sleep(0.14)
        refreshed = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.26,
                brightness=0.12,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )
        self.assertTrue(self.publisher.should_publish(refreshed))

    def test_should_publish_immediately_when_synth_changes(self) -> None:
        first = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(
                primary=HandMotion(handedness="right", active=True),
                secondary=HandMotion(handedness="left", active=True),
                hands_detected=2,
            ),
        )
        second = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="square",
                active=True,
            ),
            MotionFeatures(
                primary=HandMotion(handedness="right", active=True),
                secondary=HandMotion(handedness="left", active=True),
                hands_detected=2,
            ),
        )

        self.assertTrue(self.publisher.should_publish(first))
        self.assertTrue(self.publisher.should_publish(second))

    def test_should_publish_immediately_when_secondary_hand_appears(self) -> None:
        first = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )
        second = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(
                primary=HandMotion(handedness="right", active=True),
                secondary=HandMotion(handedness="left", active=True),
                hands_detected=2,
            ),
        )

        self.assertTrue(self.publisher.should_publish(first))
        self.assertTrue(self.publisher.should_publish(second))

    def test_should_publish_immediately_when_gesture_event_changes(self) -> None:
        first = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )
        second = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                synth_name="triangle",
                gesture_event="pinch",
                gesture_label="pinch",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )

        self.assertTrue(self.publisher.should_publish(first))
        self.assertTrue(self.publisher.should_publish(second))

    def test_should_publish_immediately_when_selected_preset_changes(self) -> None:
        first = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )

        self.publisher.set_selected_preset("angry")
        second = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                active=True,
            ),
            MotionFeatures(primary=HandMotion(handedness="right", active=True), hands_detected=1),
        )

        self.assertTrue(self.publisher.should_publish(first))
        self.assertTrue(self.publisher.should_publish(second))


class PreviewPublisherTests(unittest.TestCase):
    def test_build_frame_generates_data_url_and_respects_max_width(self) -> None:
        config = StrudelConfig(
            enabled=True,
            preview_max_width=320,
            preview_jpeg_quality=70,
        )
        publisher = PreviewPublisher(config)
        overlay = np.zeros((240, 640, 3), dtype=np.uint8)

        frame = publisher.build_frame(overlay)

        self.assertTrue(frame.image.startswith("data:image/jpeg;base64,"))
        self.assertEqual(frame.width, 320)
        self.assertGreater(frame.height, 0)

    def test_should_publish_respects_preview_rate(self) -> None:
        config = StrudelConfig(enabled=True, preview_update_hz=10)
        publisher = PreviewPublisher(config)

        self.assertTrue(publisher.should_publish())
        self.assertFalse(publisher.should_publish())

        time.sleep(0.11)
        self.assertTrue(publisher.should_publish())


class ServerFallbackTests(unittest.TestCase):
    def test_web_server_falls_back_when_preferred_port_is_unavailable(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            blocked_port = occupied.getsockname()[1]

            server = StrudelWebServer(
                host="127.0.0.1",
                port=blocked_port,
                directory=Path(PROJECT_ROOT / "web" / "strudel"),
                config_payload={"wsUrl": "ws://127.0.0.1:9000"},
                port_search_span=10,
            )

            try:
                server.start()
                self.assertNotEqual(server.base_url, f"http://127.0.0.1:{blocked_port}")
            finally:
                server.stop()

    def test_bridge_server_falls_back_when_preferred_port_is_unavailable(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            blocked_port = occupied.getsockname()[1]

            server = StrudelBridgeServer(
                host="127.0.0.1",
                port=blocked_port,
                port_search_span=10,
            )

            try:
                server.start()
                self.assertNotEqual(server.port, blocked_port)
            finally:
                server.stop()


if __name__ == "__main__":
    unittest.main()
