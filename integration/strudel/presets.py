from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from integration.strudel.scenes import get_scene, scene_summary_payload


@dataclass(slots=True, frozen=True)
class EmotionProfile:
    id: str
    emotion: str
    label: str
    description: str
    bpm: int
    density: float
    intensity: float
    gain_range: tuple[float, float]
    lpf_range: tuple[int, int]
    synth_family: tuple[str, ...]
    scale_notes: tuple[str, ...]
    rhythm_patterns: tuple[str, ...]
    variation: float
    transition_seconds: float

    @property
    def name(self) -> str:
        return self.label

    @property
    def default_synth(self) -> str:
        return self.synth_family[0]

    @property
    def rhythm_pattern(self) -> str:
        return self.rhythm_patterns[0]

    @property
    def gain_scale(self) -> float:
        return self.intensity

    @property
    def filter_offset(self) -> int:
        neutral_midpoint = 2350
        profile_midpoint = round((self.lpf_range[0] + self.lpf_range[1]) / 2)
        return profile_midpoint - neutral_midpoint

    def to_payload(self) -> dict[str, object]:
        return profile_to_public_payload(self)


# Backward-compatible name for code that still imports the first preset model.
StrudelPreset = EmotionProfile


_PROFILES: dict[str, EmotionProfile] = {
    "neutral": EmotionProfile(
        id="neutral",
        emotion="neutral",
        label="Neutro",
        description=(
            "Perfil equilibrado, com pulso estavel, densidade moderada e resposta "
            "direta aos movimentos."
        ),
        bpm=92,
        density=1.0,
        intensity=1.0,
        gain_range=(0.08, 0.65),
        lpf_range=(700, 4000),
        synth_family=("sawtooth", "triangle", "sine"),
        scale_notes=("C", "D#", "F", "G", "A#"),
        rhythm_patterns=(
            "{note}",
            "{note} ~ {note} ~",
            "{note} {note} ~ {note}",
        ),
        variation=0.30,
        transition_seconds=0.35,
    ),
    "happy": EmotionProfile(
        id="happy",
        emotion="joy",
        label="Alegria",
        description=(
            "Perfil mais rapido e luminoso, com maior densidade, variacao e "
            "abertura timbrica."
        ),
        bpm=120,
        density=1.18,
        intensity=1.08,
        gain_range=(0.10, 0.78),
        lpf_range=(1600, 7000),
        synth_family=("triangle", "sawtooth", "sine"),
        scale_notes=("C", "D", "E", "G", "A"),
        rhythm_patterns=(
            "{note} ~ {note} {note}",
            "{note} {note} ~ {note}",
            "{note} {note} {note} {note}",
        ),
        variation=0.78,
        transition_seconds=0.22,
    ),
    "sad": EmotionProfile(
        id="sad",
        emotion="sadness",
        label="Tristeza",
        description=(
            "Perfil lento e espacoso, com menor intensidade, filtro mais fechado "
            "e timbres suaves."
        ),
        bpm=68,
        density=0.74,
        intensity=0.88,
        gain_range=(0.05, 0.52),
        lpf_range=(450, 2800),
        synth_family=("sine", "triangle"),
        scale_notes=("C", "D#", "F", "G", "A#"),
        rhythm_patterns=(
            "{note} ~ ~ {note}",
            "{note} ~ {note} ~",
            "{note} ~ ~ ~",
        ),
        variation=0.22,
        transition_seconds=0.65,
    ),
    "angry": EmotionProfile(
        id="angry",
        emotion="anger",
        label="Raiva",
        description=(
            "Perfil intenso e denso, com repeticao forte, filtro aberto e familia "
            "timbrica mais aspera."
        ),
        bpm=136,
        density=1.24,
        intensity=1.16,
        gain_range=(0.14, 0.90),
        lpf_range=(2200, 8200),
        synth_family=("square", "sawtooth"),
        scale_notes=("C", "C#", "D#", "F", "G"),
        rhythm_patterns=(
            "{note} {note} {note} ~",
            "{note} {note} {note} {note}",
            "{note} {note} ~ {note} {note} ~",
        ),
        variation=0.88,
        transition_seconds=0.28,
    ),
}

_ALIASES = {
    "neutral": "neutral",
    "neutro": "neutral",
    "joy": "happy",
    "happy": "happy",
    "alegria": "happy",
    "feliz": "happy",
    "sadness": "sad",
    "sad": "sad",
    "tristeza": "sad",
    "anger": "angry",
    "angry": "angry",
    "andry": "angry",
    "raiva": "angry",
}

_PATTERN_INDEX = {
    "single": 0,
    "pulse": 1,
    "stutter": 2,
}


def list_emotion_profiles() -> list[EmotionProfile]:
    return list(_PROFILES.values())


def get_default_emotion_profile() -> EmotionProfile:
    return _PROFILES["neutral"]


def normalize_emotion_id(value: str | None) -> str:
    if not value:
        return "neutral"

    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return _ALIASES.get(normalized, "neutral")


def is_known_emotion_id(value: str | None) -> bool:
    if not value:
        return False

    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized in _ALIASES


def get_emotion_profile(profile_id: str | None) -> EmotionProfile:
    return _PROFILES[normalize_emotion_id(profile_id)]


def profile_to_public_payload(profile: EmotionProfile) -> dict[str, object]:
    return {
        "id": profile.id,
        "emotion": profile.emotion,
        "label": profile.label,
        "name": profile.name,
        "description": profile.description,
        "bpm": profile.bpm,
        "density": profile.density,
        "intensity": profile.intensity,
        "gain_range": profile.gain_range,
        "lpf_range": profile.lpf_range,
        "synth_family": profile.synth_family,
        "scale_notes": profile.scale_notes,
        "rhythm_patterns": profile.rhythm_patterns,
        "variation": profile.variation,
        "transition_seconds": profile.transition_seconds,
        "scene": scene_summary_payload(get_scene(profile.id)),
        # Compatibility fields consumed by the first preset UI/state contract.
        "rhythm_pattern": profile.rhythm_pattern,
        "default_synth": profile.default_synth,
        "gain_scale": profile.gain_scale,
        "filter_offset": profile.filter_offset,
    }


def select_rhythm_pattern(profile: EmotionProfile, pattern_mode: str) -> str:
    index = _PATTERN_INDEX.get(pattern_mode, 0)
    return profile.rhythm_patterns[index % len(profile.rhythm_patterns)]


# Legacy preset API kept while the frontend and external callers migrate.
def list_presets() -> list[EmotionProfile]:
    return list_emotion_profiles()


def default_preset() -> EmotionProfile:
    return get_default_emotion_profile()


def get_preset(preset_id: str | None) -> EmotionProfile:
    return get_emotion_profile(preset_id)
