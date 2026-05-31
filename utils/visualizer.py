from __future__ import annotations

import cv2

from utils.models import HandFrame, HandsFrame, MotionFeatures, SoundParameters

HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)

def render_overlay(
    frame,
    hand_frame: HandFrame | HandsFrame | None,
    motion: MotionFeatures,
    sound: SoundParameters,
    title: str,
):
    overlay = frame.copy()
    frame_height, frame_width = overlay.shape[:2]
    hands = _normalize_hands(hand_frame)

    for hand in hands:
        _draw_hand(
            overlay,
            hand,
            frame_width,
            frame_height,
            is_primary=motion.active and hand.handedness == motion.handedness,
        )

    if not hands:
        status = "Aproxime uma mao da camera"
        hands_status = "Maos detectadas: 0"
    else:
        label_text = ", ".join(hand.handedness for hand in hands)
        status = "Mao detectada" if len(hands) == 1 else "Duas maos detectadas"
        hands_status = f"Maos detectadas: {len(hands)} ({label_text})"

    lines = [
        title,
        status,
        hands_status,
        f"Mao primaria: {motion.handedness if motion.active else 'nenhuma'} -> nota/gain",
        (
            f"Mao secundaria: {motion.secondary_handedness} -> brilho/synth"
            if motion.has_secondary
            else "Mao secundaria: indisponivel"
        ),
        "Saida ativa: navegador + Strudel",
        f"Nota: {sound.note_label}",
        f"Frequencia: {sound.frequency:.1f} Hz",
        f"Amplitude: {sound.amplitude:.2f}",
        f"Brilho: {sound.brightness:.2f}",
        f"Synth: {sound.synth_name}",
        f"Velocidade prim.: {motion.velocity:.2f}",
        f"Abertura prim.: {motion.openness:.2f}",
        (
            f"Velocidade sec.: {motion.secondary.velocity:.2f}"
            if motion.has_secondary
            else "Velocidade sec.: --"
        ),
        (
            f"Abertura sec.: {motion.secondary.openness:.2f}"
            if motion.has_secondary
            else "Abertura sec.: --"
        ),
        "Encerramento: Ctrl+C no terminal",
    ]

    y = 30
    for line in lines:
        cv2.putText(
            overlay,
            line,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62,
            (245, 245, 245),
            2,
            cv2.LINE_AA,
        )
        y += 28

    return overlay


def _normalize_hands(hand_frame: HandFrame | HandsFrame | None) -> list[HandFrame]:
    if hand_frame is None:
        return []
    if isinstance(hand_frame, HandFrame):
        return [hand_frame]
    return hand_frame.hands


def _draw_hand(
    overlay,
    hand_frame: HandFrame,
    frame_width: int,
    frame_height: int,
    is_primary: bool,
) -> None:
    points = [
        (int(landmark.x * frame_width), int(landmark.y * frame_height))
        for landmark in hand_frame.landmarks
    ]

    line_color = (80, 220, 160) if is_primary else (255, 175, 80)
    label_background = (20, 180, 255) if is_primary else (80, 80, 240)

    for start, end in HAND_CONNECTIONS:
        cv2.line(overlay, points[start], points[end], line_color, 2)

    for index, point in enumerate(points):
        radius = 6 if index in (4, 8) else 4
        color = label_background if index == 8 else line_color
        cv2.circle(overlay, point, radius, color, -1)
        label_position = (point[0] + 8, point[1] - 8)
        cv2.putText(
            overlay,
            str(index),
            label_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (15, 15, 15),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            overlay,
            str(index),
            label_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    wrist_point = points[0]
    hand_label = hand_frame.handedness.upper()
    cv2.putText(
        overlay,
        hand_label,
        (wrist_point[0] + 12, wrist_point[1] + 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (15, 15, 15),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        hand_label,
        (wrist_point[0] + 12, wrist_point[1] + 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
