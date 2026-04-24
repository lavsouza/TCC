from __future__ import annotations

import threading
from math import tau

import numpy as np
import sounddevice as sd

from utils.config import AudioConfig
from utils.models import SoundParameters


class SoundEngine:
    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._phase = 0.0
        self._current_frequency = config.base_frequency
        self._current_amplitude = 0.0
        self._current_brightness = 0.0
        self._target_frequency = config.base_frequency
        self._target_amplitude = 0.0
        self._target_brightness = 0.0
        self._stream: sd.OutputStream | None = None

    def start(self) -> None:
        if self._stream is not None:
            return

        try:
            self._stream = sd.OutputStream(
                samplerate=self._config.sample_rate,
                blocksize=self._config.block_size,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
        except Exception as exc:
            self._stream = None
            raise RuntimeError(f"Saida de audio indisponivel: {exc}") from exc

    def update(self, params: SoundParameters) -> None:
        with self._lock:
            self._target_frequency = max(40.0, params.frequency)
            self._target_amplitude = _clamp(params.amplitude if params.active else 0.0)
            self._target_brightness = _clamp(params.brightness)

    def stop(self) -> None:
        if self._stream is None:
            return

        self._stream.stop()
        self._stream.close()
        self._stream = None

    def _audio_callback(self, outdata, frames, time_info, status) -> None:
        del time_info, status

        with self._lock:
            target_frequency = self._target_frequency
            target_amplitude = self._target_amplitude
            target_brightness = self._target_brightness

        frequency_curve = np.linspace(
            self._current_frequency,
            target_frequency,
            frames,
            endpoint=False,
        )
        amplitude_curve = np.linspace(
            self._current_amplitude,
            target_amplitude,
            frames,
            endpoint=False,
        )
        brightness_curve = np.linspace(
            self._current_brightness,
            target_brightness,
            frames,
            endpoint=False,
        )

        phase_increments = (tau * frequency_curve) / self._config.sample_rate
        phases = self._phase + np.cumsum(phase_increments)

        fundamental = np.sin(phases)
        harmonic = np.sin(phases * 2.0)
        mix = (1.0 - brightness_curve * 0.5) * fundamental
        mix += (brightness_curve * 0.5) * harmonic
        waveform = amplitude_curve * mix

        outdata[:] = waveform.astype(np.float32).reshape(-1, 1)
        self._phase = float(phases[-1] % tau)
        self._current_frequency = float(frequency_curve[-1])
        self._current_amplitude = float(amplitude_curve[-1])
        self._current_brightness = float(brightness_curve[-1])


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))
