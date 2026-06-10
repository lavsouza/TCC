from __future__ import annotations

import time
import unittest

from integration.strudel.note_adapter import to_strudel_note
from integration.strudel.preview_publisher import PreviewPublisher
from integration.strudel.presets import (
    default_preset,
    get_default_emotion_profile,
    get_emotion_profile,
    get_preset,
    list_emotion_profiles,
    list_presets,
    normalize_emotion_id,
    profile_to_public_payload,
)
from integration.strudel.publisher import StrudelPublisher
from integration.strudel.scenes import get_scene, resolve_scene_payload
import numpy as np
from utils.config import StrudelConfig
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

    def test_emotion_profile_api_exposes_the_four_categories(self) -> None:
        profiles = list_emotion_profiles()

        self.assertEqual(
            {profile.emotion for profile in profiles},
            {"neutral", "joy", "sadness", "anger"},
        )
        self.assertEqual(get_default_emotion_profile().id, "neutral")

    def test_normalizes_portuguese_english_and_legacy_ids(self) -> None:
        self.assertEqual(normalize_emotion_id("Alegria"), "happy")
        self.assertEqual(normalize_emotion_id("sadness"), "sad")
        self.assertEqual(normalize_emotion_id("RAIVA"), "angry")
        self.assertEqual(normalize_emotion_id("andry"), "angry")
        self.assertEqual(normalize_emotion_id("invalid"), "neutral")

    def test_public_payload_contains_parametric_profile_space(self) -> None:
        payload = profile_to_public_payload(get_emotion_profile("joy"))

        self.assertEqual(payload["id"], "happy")
        self.assertEqual(payload["emotion"], "joy")
        self.assertEqual(payload["label"], "Alegria")
        self.assertGreater(len(payload["rhythm_patterns"]), 1)
        self.assertEqual(len(payload["gain_range"]), 2)
        self.assertEqual(len(payload["lpf_range"]), 2)
        self.assertGreater(len(payload["synth_family"]), 1)
        self.assertIn("transition_seconds", payload)
        self.assertEqual(payload["scene"]["name"], "Movimento luminoso")
        self.assertIn("harmony", payload["scene"]["layers"])

    def test_scenes_use_distinct_layer_structures_and_sound_design(self) -> None:
        neutral = resolve_scene_payload(get_scene("neutral"), "single")
        happy = resolve_scene_payload(get_scene("happy"), "single")
        sad = resolve_scene_payload(get_scene("sad"), "single")
        angry = resolve_scene_payload(get_scene("angry"), "single")

        self.assertEqual(
            [layer["id"] for layer in neutral["layers"]],
            ["melody", "bass", "drums"],
        )
        self.assertIn("harmony", [layer["id"] for layer in happy["layers"]])
        self.assertIn("mist", [layer["id"] for layer in sad["layers"]])
        self.assertIn("edge", [layer["id"] for layer in angry["layers"]])
        self.assertGreater(sad["layers"][0]["room"], happy["layers"][0]["room"])
        self.assertGreater(angry["layers"][0]["distort"], 0)
        self.assertIsNotNone(happy["layers"][2]["euclid"])
        self.assertGreater(neutral["master_gain"], 1.0)
        self.assertGreater(happy["master_gain"], 1.0)
        self.assertGreater(sad["master_gain"], happy["master_gain"])
        self.assertLess(angry["master_gain"], neutral["master_gain"])
        self.assertEqual(angry["continuous_update_ms"], 240)
        self.assertEqual(angry["inactive_grace_ms"], 520)
        self.assertFalse(angry["synth_change_priority"])
        self.assertGreater(angry["layers"][0]["release"], 0.1)
        self.assertEqual(angry["mode_action"], "none")

    def test_scene_variations_are_deterministic_for_reproducible_tests(self) -> None:
        first = resolve_scene_payload(get_scene("angry"), "stutter")
        second = resolve_scene_payload(get_scene("angry"), "stutter")

        self.assertEqual(first, second)


class StrudelPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = StrudelConfig(
            update_hz=8,
            gain_delta=0.03,
            brightness_delta=0.05,
        )
        self.publisher = StrudelPublisher(self.config)

    def test_build_state_generates_expected_profile_scene_and_filter(self) -> None:
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
        self.assertEqual(state.lpf, 2680)
        self.assertEqual(state.synth, "square")
        self.assertEqual(state.primary_handedness, "right")
        self.assertEqual(state.secondary_handedness, "left")
        self.assertEqual(state.brightness_source, "left")
        self.assertEqual(state.gesture_phase, "pinch")
        self.assertEqual(state.gesture_event, "pinch")
        self.assertEqual(state.gesture_label, "pinch")
        self.assertEqual(state.pattern_mode, "pulse")
        self.assertEqual(state.selected_preset, "happy")
        self.assertEqual(state.preset_name, "Alegria")
        self.assertEqual(state.preset_source, "manual")
        self.assertEqual(state.emotion, "joy")
        self.assertEqual(state.emotion_label, "Alegria")
        self.assertEqual(state.emotion_source, "manual")
        self.assertEqual(state.emotion_confidence, 1.0)
        self.assertEqual(state.selected_profile, "happy")
        self.assertEqual(state.profile_name, "Alegria")
        self.assertEqual(state.profile_gain_range, (0.10, 0.78))
        self.assertEqual(state.profile_lpf_range, (1600, 7000))
        self.assertEqual(state.scene_name, "Movimento luminoso")
        self.assertIn("harmony", state.scene_layers)
        self.assertEqual(state.scene["gesture"]["pinch_gain"], 1.22)
        self.assertEqual(state.scene["layers"][2]["euclid"], (3, 8, 0))
        self.assertEqual(state.code, "")

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
        self.assertEqual(payload["preset_name"], "Tristeza")
        self.assertEqual(payload["preset_source"], "manual")
        self.assertEqual(payload["emotion"], "sadness")
        self.assertEqual(payload["emotion_source"], "manual")
        self.assertEqual(payload["emotion_confidence"], 1.0)
        self.assertEqual(payload["selected_profile"], "sad")
        self.assertEqual(payload["profile_name"], "Tristeza")
        self.assertIn("profile_rhythm_patterns", payload)
        self.assertIn("profile_transition_seconds", payload)
        self.assertEqual(payload["scene_name"], "Espaco suspenso")
        self.assertIn("harmony", payload["scene_layers"])
        self.assertEqual(payload["scene"]["beats_per_cycle"], 4)
        self.assertEqual(payload["type"], "state")

    def test_build_state_keeps_legacy_code_field_empty(self) -> None:
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
        self.assertEqual(state.code, "")

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
        self.assertEqual(state.preset_name, "Neutro")
        self.assertEqual(state.selected_profile, "neutral")
        self.assertEqual(state.emotion, "neutral")

    def test_profile_changes_generated_pattern_without_removing_gesture_control(self) -> None:
        params = SoundParameters(
            frequency=261.6,
            amplitude=0.30,
            brightness=0.40,
            note_label="C4",
            synth_name="square",
            pattern_mode="pulse",
            active=True,
        )
        motion = MotionFeatures(
            primary=HandMotion(handedness="right", active=True),
            secondary=HandMotion(handedness="left", active=True),
            hands_detected=2,
        )

        self.publisher.set_selected_profile("joy")
        happy = self.publisher.build_state(params, motion)
        self.publisher.set_selected_profile("sadness")
        sad = self.publisher.build_state(params, motion)

        self.assertNotEqual(happy.profile_rhythm, sad.profile_rhythm)
        self.assertGreater(happy.profile_bpm, sad.profile_bpm)
        self.assertGreater(happy.lpf, sad.lpf)
        self.assertEqual(happy.synth, "square")
        self.assertEqual(sad.synth, "square")
        self.assertEqual(happy.scene_name, "Movimento luminoso")
        self.assertEqual(sad.scene_name, "Espaco suspenso")
        self.assertEqual(happy.scene["layers"][1]["intervals"], "[0,4,7]")
        self.assertEqual(sad.scene["layers"][1]["intervals"], "[0,3,7]")
        self.assertEqual(happy.scene["layers"][4]["euclid"], (5, 8, 1))
        self.assertEqual(sad.scene["layers"][4]["room"], 0.90)
        self.assertEqual(sad.code, "")

    def test_angry_scene_uses_dense_rhythm_and_distortion(self) -> None:
        self.publisher.set_selected_profile("angry")
        state = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.30,
                brightness=0.50,
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

        self.assertEqual(state.scene_name, "Pressao fragmentada")
        self.assertEqual(state.scene["layers"][2]["pattern"], "bd*4, [~ sd]*2, hh*16")
        self.assertEqual(state.scene["layers"][1]["distort"], 0.72)
        self.assertEqual(state.scene["layers"][0]["crush"], 7)
        self.assertEqual(state.scene["layers"][1]["euclid"], (5, 8, 0))
        self.assertEqual(state.scene["layers"][0]["release"], 0.18)
        self.assertEqual(state.scene["mode_action"], "none")

    def test_hold_gesture_uses_profile_specific_layer(self) -> None:
        params = SoundParameters(
            frequency=261.6,
            amplitude=0.30,
            brightness=0.30,
            note_label="C4",
            gesture_phase="hold",
            gesture_event="hold",
            gesture_label="hold",
            active=True,
        )
        motion = MotionFeatures(
            primary=HandMotion(handedness="right", active=True),
            hands_detected=1,
        )

        self.publisher.set_selected_profile("sad")
        sad = self.publisher.build_state(params, motion)
        self.publisher.set_selected_profile("angry")
        angry = self.publisher.build_state(params, motion)

        self.assertEqual(sad.scene["gesture"]["hold_layer"]["id"], "hold_drone")
        self.assertEqual(sad.scene["gesture"]["hold_layer"]["release"], 3.0)
        self.assertEqual(sad.scene["gesture"]["hold_layer"]["room"], 0.92)
        self.assertEqual(angry.scene["gesture"]["hold_layer"]["id"], "hold_pressure")
        self.assertEqual(angry.scene["gesture"]["hold_layer"]["distort"], 0.95)
        self.assertEqual(angry.scene["gesture"]["hold_layer"]["crush"], 5)

    def test_motion_values_still_modulate_gain_and_lpf_inside_profile(self) -> None:
        self.publisher.set_selected_profile("neutral")
        motion = MotionFeatures(
            primary=HandMotion(handedness="right", active=True),
            hands_detected=1,
        )
        quiet = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.20,
                brightness=0.10,
                note_label="C4",
                active=True,
            ),
            motion,
        )
        expressive = self.publisher.build_state(
            SoundParameters(
                frequency=392.0,
                amplitude=0.50,
                brightness=0.80,
                note_label="G4",
                active=True,
            ),
            motion,
        )

        self.assertEqual(quiet.strudel_note, "c4")
        self.assertEqual(expressive.strudel_note, "g4")
        self.assertGreater(expressive.gain, quiet.gain)
        self.assertGreater(expressive.lpf, quiet.lpf)

    def test_classifier_source_is_supported_without_classifier_implementation(self) -> None:
        self.publisher.set_selected_profile(
            "anger",
            source="classifier",
            confidence=0.73,
        )
        state = self.publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.3,
                brightness=0.2,
                note_label="C4",
                active=True,
            ),
            MotionFeatures(
                primary=HandMotion(handedness="right", active=True),
                hands_detected=1,
            ),
        )

        self.assertEqual(state.selected_profile, "angry")
        self.assertEqual(state.emotion, "anger")
        self.assertEqual(state.emotion_source, "classifier")
        self.assertEqual(state.emotion_confidence, 0.73)

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

    def test_can_defer_note_change_when_immediate_mode_is_disabled(self) -> None:
        publisher = StrudelPublisher(
            StrudelConfig(
                note_change_immediate=False,
                update_hz=1,
                gain_delta=1.0,
                brightness_delta=1.0,
            )
        )
        motion = MotionFeatures(
            primary=HandMotion(handedness="right", active=True),
            hands_detected=1,
        )
        first = publisher.build_state(
            SoundParameters(
                frequency=261.6,
                amplitude=0.25,
                brightness=0.10,
                note_label="C4",
                active=True,
            ),
            motion,
        )
        second = publisher.build_state(
            SoundParameters(
                frequency=293.7,
                amplitude=0.25,
                brightness=0.10,
                note_label="D4",
                active=True,
            ),
            motion,
        )

        self.assertTrue(publisher.should_publish(first))
        self.assertFalse(publisher.should_publish(second))

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
        config = StrudelConfig(preview_update_hz=10)
        publisher = PreviewPublisher(config)

        self.assertTrue(publisher.should_publish())
        self.assertFalse(publisher.should_publish())

        time.sleep(0.11)
        self.assertTrue(publisher.should_publish())


if __name__ == "__main__":
    unittest.main()
