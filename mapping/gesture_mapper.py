from __future__ import annotations

from utils.config import MappingConfig
from utils.models import HandMotion, MotionFeatures, ScaleNote, SoundParameters

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


class GestureMapper:
    def __init__(self, config: MappingConfig) -> None:
        self._config = config
        self._scale = self._build_scale()
        self._pattern_mode_index = 0

    def map(self, motion: MotionFeatures) -> SoundParameters:
        pattern_mode = self._update_pattern_mode(motion)

        if not motion.active:
            return SoundParameters(
                frequency=0.0,
                amplitude=0.0,
                brightness=0.0,
                note_label="--",
                synth_name=self._config.default_synth_name,
                gesture_phase=motion.gesture_phase,
                gesture_event=motion.gesture_event,
                gesture_label=motion.gesture_label,
                sweep_direction=motion.sweep_direction,
                pattern_mode=pattern_mode,
                active=False,
            )

        primary = motion.primary
        modulator = motion.secondary if motion.secondary.active else motion.primary

        note_index = round(primary.x * (len(self._scale) - 1))
        note = self._scale[note_index]

        amplitude_span = self._config.max_amplitude - self._config.min_amplitude
        amplitude = self._config.min_amplitude + (1.0 - primary.y) * amplitude_span
        brightness = _clamp(
            (modulator.velocity * self._config.velocity_weight)
            + (modulator.openness * self._config.openness_weight)
        )
        synth_name = self._select_synth(motion.secondary)

        return SoundParameters(
            frequency=note.frequency,
            amplitude=amplitude,
            brightness=brightness,
            note_label=note.label,
            synth_name=synth_name,
            gesture_phase=motion.gesture_phase,
            gesture_event=motion.gesture_event,
            gesture_label=motion.gesture_label,
            sweep_direction=motion.sweep_direction,
            pattern_mode=pattern_mode,
            active=True,
        )

    def _build_scale(self) -> list[ScaleNote]:
        notes: list[ScaleNote] = []

        for octave in range(self._config.octaves):
            base_midi = self._config.root_midi + (octave * 12)
            for interval in self._config.scale_intervals:
                midi = base_midi + interval
                notes.append(
                    ScaleNote(
                        midi=midi,
                        label=_midi_to_label(midi),
                        frequency=_midi_to_frequency(midi),
                    )
                )

        return notes

    def _select_synth(self, secondary: HandMotion) -> str:
        if not secondary.active:
            return self._config.default_synth_name

        synths = self._config.secondary_synths
        if not synths:
            return self._config.default_synth_name

        synth_index = round(secondary.x * (len(synths) - 1))
        return synths[synth_index]

    def _update_pattern_mode(self, motion: MotionFeatures) -> str:
        modes = self._config.pattern_modes
        if not modes:
            return "single"

        if motion.gesture_event == "sweep":
            step = 1 if motion.sweep_direction != "left" else -1
            self._pattern_mode_index = (self._pattern_mode_index + step) % len(modes)

        return modes[self._pattern_mode_index]


def _midi_to_frequency(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12))


def _midi_to_label(midi: int) -> str:
    note_name = NOTE_NAMES[midi % 12]
    octave = (midi // 12) - 1
    return f"{note_name}{octave}"


def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))
