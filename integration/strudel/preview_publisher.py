from __future__ import annotations

import base64
import time

import cv2

from integration.strudel.models import PreviewFrame
from utils.config import StrudelConfig


class PreviewPublisher:
    def __init__(self, config: StrudelConfig) -> None:
        self._config = config
        self._last_publish_at = 0.0

    def should_publish(self) -> bool:
        now = time.perf_counter()
        interval = 1.0 / max(self._config.preview_update_hz, 1)
        if (now - self._last_publish_at) < interval:
            return False

        self._last_publish_at = now
        return True

    def build_frame(self, overlay) -> PreviewFrame:
        preview = self._resize_if_needed(overlay)
        success, encoded = cv2.imencode(
            ".jpg",
            preview,
            [int(cv2.IMWRITE_JPEG_QUALITY), self._config.preview_jpeg_quality],
        )
        if not success:
            raise RuntimeError("Nao foi possivel codificar o preview da camera.")

        image_base64 = base64.b64encode(encoded.tobytes()).decode("ascii")
        height, width = preview.shape[:2]
        return PreviewFrame(
            image=f"data:image/jpeg;base64,{image_base64}",
            width=width,
            height=height,
            timestamp=time.time(),
        )

    def _resize_if_needed(self, overlay):
        height, width = overlay.shape[:2]
        max_width = max(self._config.preview_max_width, 1)
        if width <= max_width:
            return overlay

        scale = max_width / width
        resized_size = (max_width, max(1, round(height * scale)))
        return cv2.resize(overlay, resized_size, interpolation=cv2.INTER_AREA)
