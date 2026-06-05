from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class StrudelPreset:
    id: str
    name: str
    description: str
    bpm: int
    rhythm_pattern: str
    default_synth: str
    scale_notes: tuple[str, ...]
    gain_scale: float
    filter_offset: int
    density: float

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


_PRESETS: dict[str, StrudelPreset] = {
    "neutral": StrudelPreset(
        id="neutral",
        name="Neutral",
        description="Camada equilibrada para exploracao geral, com pulso estavel e resposta direta ao gesto.",
        bpm=92,
        rhythm_pattern="{note}",
        default_synth="sawtooth",
        scale_notes=("C", "D#", "F", "G", "A#"),
        gain_scale=1.0,
        filter_offset=0,
        density=1.0,
    ),
    "happy": StrudelPreset(
        id="happy",
        name="Happy",
        description="Preset mais animado, com repeticoes leves e maior abertura timbrica.",
        bpm=120,
        rhythm_pattern="{note} {note} ~ {note}",
        default_synth="triangle",
        scale_notes=("C", "D", "E", "G", "A"),
        gain_scale=1.08,
        filter_offset=550,
        density=1.18,
    ),
    "sad": StrudelPreset(
        id="sad",
        name="Sad",
        description="Preset mais lento e espacoso, com menor densidade e timbre mais suave.",
        bpm=68,
        rhythm_pattern="{note} ~ ~ {note}",
        default_synth="sine",
        scale_notes=("C", "D#", "F", "G", "A#"),
        gain_scale=0.88,
        filter_offset=-280,
        density=0.74,
    ),
    "angry": StrudelPreset(
        id="angry",
        name="Angry",
        description="Preset agressivo e denso, com repeticao insistente e maior energia ritmica.",
        bpm=136,
        rhythm_pattern="{note} {note} {note} ~",
        default_synth="square",
        scale_notes=("C", "C#", "D#", "F", "G"),
        gain_scale=1.16,
        filter_offset=900,
        density=1.32,
    ),
}

_ALIASES = {
}


def list_presets() -> list[StrudelPreset]:
    return list(_PRESETS.values())


def default_preset() -> StrudelPreset:
    return _PRESETS["neutral"]


def get_preset(preset_id: str | None) -> StrudelPreset:
    if not preset_id:
        return default_preset()

    normalized = _ALIASES.get(preset_id.lower(), preset_id.lower())
    return _PRESETS.get(normalized, default_preset())
