from __future__ import annotations

import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp

from utils.config import CameraConfig
from utils.models import HandFrame, HandsFrame, Landmark


class HandTracker:
    def __init__(self, config: CameraConfig) -> None:
        self._config = config
        self._capture = self._open_capture(config.device_index)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)
        self._hands = self._create_landmarker(config)

    def read(self) -> tuple[object, HandsFrame | None]:
        ok, frame = self._capture.read()
        if not ok or frame is None:
            raise RuntimeError("Nao foi possivel ler um frame da camera.")

        if self._config.mirror_feed:
            frame = cv2.flip(frame, 1)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.perf_counter() * 1000)
        result = self._hands.detect_for_video(mp_image, timestamp_ms)
        hands_frame = self._extract_hands(result)
        return frame, hands_frame

    def close(self) -> None:
        self._capture.release()
        self._hands.close()

    @staticmethod
    def _create_landmarker(config: CameraConfig):
        model_path = _ensure_model_file(config.model_path, config.model_url)
        base_options = mp.tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=config.max_num_hands,
            min_hand_detection_confidence=config.min_detection_confidence,
            min_hand_presence_confidence=config.min_presence_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
        )
        return mp.tasks.vision.HandLandmarker.create_from_options(options)

    @staticmethod
    def _open_capture(device_index: int) -> cv2.VideoCapture:
        backend = getattr(cv2, "CAP_DSHOW", None)

        if backend is not None:
            capture = cv2.VideoCapture(device_index, backend)
            if capture.isOpened():
                return capture
            capture.release()

        capture = cv2.VideoCapture(device_index)
        if not capture.isOpened():
            raise RuntimeError(
                f"Camera {device_index} nao pode ser aberta. "
                "Verifique permissao de camera e dispositivo selecionado."
            )
        return capture

    @staticmethod
    def _extract_hands(result: object) -> HandsFrame | None:
        landmarks_data = getattr(result, "hand_landmarks", None)
        if not landmarks_data:
            return None

        handedness_data = getattr(result, "handedness", None)
        frame_timestamp = time.perf_counter()
        hands: list[HandFrame] = []

        for index, hand_landmarks in enumerate(landmarks_data):
            landmarks = [
                Landmark(x=point.x, y=point.y, z=point.z)
                for point in hand_landmarks
            ]

            handedness = "unknown"
            if handedness_data and index < len(handedness_data) and handedness_data[index]:
                handedness = handedness_data[index][0].category_name.lower()

            hands.append(
                HandFrame(
                    landmarks=landmarks,
                    handedness=handedness,
                    timestamp=frame_timestamp,
                )
            )

        hands.sort(key=lambda hand: hand.anchor_x)
        return HandsFrame(hands=hands, timestamp=frame_timestamp)


def _ensure_model_file(model_path: Path, model_url: str) -> Path:
    if model_path.exists():
        return model_path

    model_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        urllib.request.urlretrieve(model_url, model_path)
    except Exception as exc:
        raise RuntimeError(
            "Nao foi possivel baixar o modelo do MediaPipe automaticamente. "
            f"Baixe manualmente em {model_url} e salve em {model_path}."
        ) from exc

    return model_path
