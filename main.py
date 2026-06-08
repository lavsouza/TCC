from __future__ import annotations

from capture.hand_tracker import HandTracker
from integration.strudel.output import StrudelOutput
from mapping.gesture_mapper import GestureMapper
from processing.movement_processor import MovementProcessor
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
    strudel_output = StrudelOutput(config.strudel)

    try:
        if not strudel_output.enabled:
            print("[erro] A saida Strudel precisa estar habilitada nesta versao do prototipo.")
            return 1

        try:
            strudel_output.start()
        except RuntimeError as exc:
            print(f"[erro] {exc}")
            return 1

        print(f"[info] Strudel disponivel em {strudel_output.web_url}")
        print("[info] Abra a interface no navegador e use Ctrl+C no terminal para encerrar.")

        while True:
            frame, hands_frame = tracker.read()
            motion = processor.process(hands_frame)
            sound_params = mapper.map(motion)

            overlay = render_overlay(
                frame=frame,
                hand_frame=hands_frame,
                motion=motion,
            )
            strudel_output.publish_state(motion, sound_params)
            strudel_output.publish_preview(overlay)

        return 0
    except KeyboardInterrupt:
        print("\n[info] Encerrando o prototipo...")
        return 0
    finally:
        tracker.close()
        strudel_output.stop()


if __name__ == "__main__":
    raise SystemExit(main())
