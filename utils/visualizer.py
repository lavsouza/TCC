from __future__ import annotations

import cv2

from utils.models import HandFrame, MotionFeatures, SoundParameters

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
    hand_frame: HandFrame | None,
    motion: MotionFeatures,
    sound: SoundParameters,
    audio_enabled: bool,
    window_name: str,
):
    overlay = frame.copy()
    frame_height, frame_width = overlay.shape[:2]

    if hand_frame is not None:
        _draw_hand(overlay, hand_frame, frame_width, frame_height)

    status = "Mao detectada" if hand_frame else "Aproxime uma mao da camera"
    audio_status = "Audio ativo" if audio_enabled else "Audio desabilitado"

    lines = [
        window_name,
        status,
        audio_status,
        f"Nota: {sound.note_label}",
        f"Frequencia: {sound.frequency:.1f} Hz",
        f"Amplitude: {sound.amplitude:.2f}",
        f"Brilho: {sound.brightness:.2f}",
        f"Velocidade: {motion.velocity:.2f}",
        f"Abertura: {motion.openness:.2f}",
        "Sair: q ou esc",
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


def _draw_hand(
    overlay,
    hand_frame: HandFrame,
    frame_width: int,
    frame_height: int,
) -> None:
    points = [
        (int(landmark.x * frame_width), int(landmark.y * frame_height))
        for landmark in hand_frame.landmarks
    ]

    for start, end in HAND_CONNECTIONS:
        cv2.line(overlay, points[start], points[end], (80, 220, 160), 2)

    for index, point in enumerate(points):
        radius = 6 if index in (4, 8) else 4
        color = (20, 180, 255) if index == 8 else (255, 180, 60)
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
