from __future__ import annotations

import cv2

from capture.hand_tracker import HandTracker
from mapping.gesture_mapper import GestureMapper
from processing.movement_processor import MovementProcessor
from sound.sound_engine import SoundEngine
from utils.config import load_config
from utils.visualizer import render_overlay


def main() -> int:
    config = load_config()

    try:
        tracker = HandTracker(config.camera)
    except RuntimeError as exc:
        print(f"[erro] {exc}")
        return 1

    processor = MovementProcessor(config.processing)
    mapper = GestureMapper(config.mapping)
    sound_engine = SoundEngine(config.audio)
    audio_enabled = True

    try:
        try:
            sound_engine.start()
        except RuntimeError as exc:
            audio_enabled = False
            print(f"[aviso] {exc}")
            print("[aviso] O prototipo seguira apenas com feedback visual.")

        while True:
            frame, hand_frame = tracker.read()
            motion = processor.process(hand_frame)
            sound_params = mapper.map(motion)

            if audio_enabled:
                sound_engine.update(sound_params)

            overlay = render_overlay(
                frame=frame,
                hand_frame=hand_frame,
                motion=motion,
                sound=sound_params,
                audio_enabled=audio_enabled,
                window_name=config.ui.window_name,
            )
            cv2.imshow(config.ui.window_name, overlay)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break

        return 0
    finally:
        tracker.close()
        sound_engine.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    raise SystemExit(main())
