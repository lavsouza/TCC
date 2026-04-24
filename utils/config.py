from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(slots=True)
class CameraConfig:
    device_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    mirror_feed: bool = True
    max_num_hands: int = 1
    min_detection_confidence: float = 0.65
    min_presence_confidence: float = 0.5
    min_tracking_confidence: float = 0.55
    model_path: Path = PROJECT_ROOT / "models" / "hand_landmarker.task"
    model_url: str = (
        "https://storage.googleapis.com/mediapipe-models/"
        "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    )


@dataclass(slots=True)
class ProcessingConfig:
    position_smoothing: float = 0.3
    velocity_smoothing: float = 0.25
    openness_smoothing: float = 0.2
    velocity_reference: float = 1.3
    hand_span_reference: float = 2.2


@dataclass(slots=True)
class MappingConfig:
    root_midi: int = 48
    octaves: int = 3
    scale_intervals: tuple[int, ...] = (0, 3, 5, 7, 10)
    min_amplitude: float = 0.08
    max_amplitude: float = 0.65
    velocity_weight: float = 0.6
    openness_weight: float = 0.4


@dataclass(slots=True)
class AudioConfig:
    sample_rate: int = 44100
    block_size: int = 512
    base_frequency: float = 220.0


@dataclass(slots=True)
class UiConfig:
    window_name: str = "MoveCodeBeats"


@dataclass(slots=True)
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    mapping: MappingConfig = field(default_factory=MappingConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    ui: UiConfig = field(default_factory=UiConfig)


def load_config() -> AppConfig:
    return AppConfig()
