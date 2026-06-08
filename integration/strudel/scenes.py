from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class LayerRecipe:
    id: str
    kind: str
    patterns: tuple[str, str, str]
    sound: str
    use_motion_synth: bool = False
    note_offset: int = 0
    intervals: str = ""
    gain: float = 1.0
    follow_filter: bool = True
    lpf_ratio: float = 1.0
    hpf: int = 0
    attack: float = 0.0
    release: float = 0.0
    room: float = 0.0
    delay: float = 0.0
    delay_time: float = 0.0
    shape: float = 0.0
    distort: float = 0.0
    crush: int = 0
    pan: str = ""
    fast: float = 1.0
    slow: float = 1.0
    euclid: tuple[int, int, int] | None = None
    palindrome: bool = False


@dataclass(slots=True, frozen=True)
class GestureRecipe:
    pinch_gain: float
    pinch_lpf_offset: int
    pinch_fast: float
    pinch_shape: float
    release_gain: float
    release_room: float
    release_delay: float
    hold_layer: LayerRecipe
    sweep_left: str
    sweep_right: str
    sweep_amount: float


@dataclass(slots=True, frozen=True)
class SceneRecipe:
    id: str
    name: str
    description: str
    beats_per_cycle: int
    master_gain: float
    continuous_update_ms: int
    inactive_grace_ms: int
    synth_change_priority: bool
    layers: tuple[LayerRecipe, ...]
    mode_actions: tuple[str, str, str]
    mode_amounts: tuple[float, float, float]
    mode_layer_gain: float
    gesture: GestureRecipe


_SCENES: dict[str, SceneRecipe] = {
    "neutral": SceneRecipe(
        id="neutral",
        name="Pulso equilibrado",
        description=(
            "Melodia central, baixo discreto e bateria regular com pouca "
            "ambiencia."
        ),
        beats_per_cycle=4,
        master_gain=1.55,
        continuous_update_ms=150,
        inactive_grace_ms=360,
        synth_change_priority=True,
        layers=(
            LayerRecipe(
                id="melody",
                kind="note",
                patterns=(
                    "{note} ~ {note} ~",
                    "{note} ~ {note} {note}",
                    "{note} {note} ~ {note}",
                ),
                sound="sawtooth",
                use_motion_synth=True,
                gain=0.78,
                release=0.28,
                room=0.12,
                pan="<0.45 0.55>",
            ),
            LayerRecipe(
                id="bass",
                kind="note",
                patterns=(
                    "{note} ~ ~ ~",
                    "{note} ~ {note} ~",
                    "{note} {note} ~ ~",
                ),
                sound="sine",
                note_offset=-12,
                gain=0.34,
                lpf_ratio=0.48,
                release=0.48,
            ),
            LayerRecipe(
                id="drums",
                kind="sample",
                patterns=(
                    "bd ~ sd ~, hh*4",
                    "bd [~ bd] sd ~, hh*6",
                    "bd*2 ~ sd ~, hh*8",
                ),
                sound="",
                gain=0.32,
                follow_filter=False,
            ),
        ),
        mode_actions=("none", "fast", "stutter"),
        mode_amounts=(1.0, 1.08, 2.0),
        mode_layer_gain=0.24,
        gesture=GestureRecipe(
            pinch_gain=1.15,
            pinch_lpf_offset=350,
            pinch_fast=1.0,
            pinch_shape=0.0,
            release_gain=0.74,
            release_room=0.16,
            release_delay=0.0,
            hold_layer=LayerRecipe(
                id="hold_pulse",
                kind="note",
                patterns=("{note} ~ ~ ~",) * 3,
                sound="sine",
                note_offset=-12,
                gain=0.22,
                lpf_ratio=0.42,
                attack=0.35,
                release=1.2,
                room=0.35,
                slow=2.0,
            ),
            sweep_left="rev",
            sweep_right="palindrome",
            sweep_amount=1.0,
        ),
    ),
    "happy": SceneRecipe(
        id="happy",
        name="Movimento luminoso",
        description=(
            "Arpejos ascendentes, harmonia maior, baixo sincopado, bateria "
            "aberta e textura aguda."
        ),
        beats_per_cycle=4,
        master_gain=1.45,
        continuous_update_ms=140,
        inactive_grace_ms=360,
        synth_change_priority=True,
        layers=(
            LayerRecipe(
                id="melody",
                kind="note",
                patterns=(
                    "{note} [{note} {note}] {note} [{note} ~]",
                    "{note} {note} [{note} {note}] {note}",
                    "[{note} {note}]*2 {note} [{note} {note}]",
                ),
                sound="triangle",
                use_motion_synth=True,
                gain=0.68,
                release=0.18,
                room=0.24,
                delay=0.12,
                delay_time=0.125,
                pan="<0.2 0.8>",
                palindrome=True,
            ),
            LayerRecipe(
                id="harmony",
                kind="note",
                patterns=(
                    "{note} ~ {note} ~",
                    "{note} {note} ~ {note}",
                    "{note}*2 ~ {note}",
                ),
                sound="triangle",
                intervals="[0,4,7]",
                gain=0.20,
                lpf_ratio=0.82,
                attack=0.06,
                release=0.45,
                room=0.38,
                pan="<0.75 0.25>",
            ),
            LayerRecipe(
                id="bass",
                kind="note",
                patterns=("{note}", "{note}", "{note}"),
                sound="sine",
                note_offset=-12,
                gain=0.30,
                lpf_ratio=0.44,
                release=0.22,
                euclid=(3, 8, 0),
            ),
            LayerRecipe(
                id="drums",
                kind="sample",
                patterns=(
                    "bd ~ sd [~ cp], hh*8, ~ oh ~ oh",
                    "bd [~ bd] sd cp, hh*8, ~ oh*2 ~",
                    "bd*2 sd [~ cp], hh*12, oh(3,8)",
                ),
                sound="",
                gain=0.36,
                follow_filter=False,
                room=0.10,
            ),
            LayerRecipe(
                id="sparkle",
                kind="note",
                patterns=("{note}", "{note}", "{note}"),
                sound="sine",
                note_offset=12,
                gain=0.10,
                lpf_ratio=1.15,
                release=0.12,
                room=0.42,
                delay=0.24,
                delay_time=0.125,
                pan="<0 1>",
                euclid=(5, 8, 1),
            ),
        ),
        mode_actions=("palindrome", "fast", "stutter"),
        mode_amounts=(1.0, 1.18, 3.0),
        mode_layer_gain=0.18,
        gesture=GestureRecipe(
            pinch_gain=1.22,
            pinch_lpf_offset=900,
            pinch_fast=1.12,
            pinch_shape=0.08,
            release_gain=0.84,
            release_room=0.42,
            release_delay=0.18,
            hold_layer=LayerRecipe(
                id="hold_shimmer",
                kind="note",
                patterns=("{note}",) * 3,
                sound="triangle",
                note_offset=12,
                gain=0.16,
                lpf_ratio=1.2,
                release=0.25,
                room=0.55,
                delay=0.28,
                delay_time=0.125,
                pan="<0 1>",
                euclid=(7, 12, 2),
            ),
            sweep_left="rev",
            sweep_right="palindrome",
            sweep_amount=1.0,
        ),
    ),
    "sad": SceneRecipe(
        id="sad",
        name="Espaco suspenso",
        description=(
            "Notas longas, acorde menor, baixo lento e grande profundidade de "
            "reverb e delay."
        ),
        beats_per_cycle=4,
        master_gain=1.75,
        continuous_update_ms=180,
        inactive_grace_ms=500,
        synth_change_priority=True,
        layers=(
            LayerRecipe(
                id="melody",
                kind="note",
                patterns=(
                    "{note}@3 ~",
                    "{note}@2 ~ {note}",
                    "{note} ~ ~ {note}",
                ),
                sound="sine",
                use_motion_synth=True,
                gain=0.64,
                lpf_ratio=0.78,
                attack=0.38,
                release=1.5,
                room=0.62,
                delay=0.18,
                delay_time=0.5,
                slow=1.5,
                pan="<0.4 0.6>",
            ),
            LayerRecipe(
                id="harmony",
                kind="note",
                patterns=("{note} ~ ~ ~",) * 3,
                sound="triangle",
                intervals="[0,3,7]",
                gain=0.20,
                lpf_ratio=0.60,
                attack=0.85,
                release=2.2,
                room=0.82,
                slow=2.0,
            ),
            LayerRecipe(
                id="bass",
                kind="note",
                patterns=("{note} ~ ~ ~",) * 3,
                sound="sine",
                note_offset=-12,
                gain=0.28,
                lpf_ratio=0.38,
                attack=0.18,
                release=1.4,
                room=0.28,
                slow=2.0,
            ),
            LayerRecipe(
                id="drums",
                kind="sample",
                patterns=(
                    "bd ~ ~ ~, ~ ~ rim ~",
                    "bd ~ ~ rim, ~ hh ~ ~",
                    "bd ~ rim ~, hh(3,8)",
                ),
                sound="",
                gain=0.18,
                follow_filter=False,
                release=0.8,
                room=0.58,
            ),
            LayerRecipe(
                id="mist",
                kind="note",
                patterns=("{note} ~ ~ ~",) * 3,
                sound="sine",
                note_offset=12,
                gain=0.08,
                lpf_ratio=0.68,
                attack=1.2,
                release=2.5,
                room=0.90,
                delay=0.35,
                delay_time=0.75,
                pan="<0.2 0.8>",
                slow=2.0,
            ),
        ),
        mode_actions=("slow", "palindrome", "stutter"),
        mode_amounts=(1.08, 1.0, 1.5),
        mode_layer_gain=0.12,
        gesture=GestureRecipe(
            pinch_gain=1.05,
            pinch_lpf_offset=120,
            pinch_fast=0.90,
            pinch_shape=0.0,
            release_gain=0.70,
            release_room=0.88,
            release_delay=0.34,
            hold_layer=LayerRecipe(
                id="hold_drone",
                kind="note",
                patterns=("{note}",) * 3,
                sound="sine",
                note_offset=-12,
                intervals="[0,7]",
                gain=0.18,
                lpf_ratio=0.35,
                attack=1.4,
                release=3.0,
                room=0.92,
                delay=0.25,
                delay_time=1.0,
                slow=4.0,
            ),
            sweep_left="slow",
            sweep_right="palindrome",
            sweep_amount=1.35,
        ),
    ),
    "angry": SceneRecipe(
        id="angry",
        name="Pressao fragmentada",
        description=(
            "Baixo agressivo, repeticoes euclidianas, bateria densa e "
            "distorcao controlada."
        ),
        beats_per_cycle=4,
        master_gain=1.30,
        continuous_update_ms=240,
        inactive_grace_ms=520,
        synth_change_priority=False,
        layers=(
            LayerRecipe(
                id="melody",
                kind="note",
                patterns=(
                    "{note}*4 [{note} {note}] {note}*2 ~",
                    "{note}*6 ~ {note}*2",
                    "[{note} {note}]*4",
                ),
                sound="square",
                use_motion_synth=True,
                gain=0.62,
                lpf_ratio=1.10,
                hpf=100,
                release=0.18,
                shape=0.34,
                distort=0.55,
                crush=7,
                fast=1.08,
                pan="<0.15 0.85>",
            ),
            LayerRecipe(
                id="bass",
                kind="note",
                patterns=("{note}", "{note}", "{note}"),
                sound="sawtooth",
                note_offset=-12,
                gain=0.46,
                lpf_ratio=0.70,
                hpf=55,
                release=0.24,
                shape=0.45,
                distort=0.72,
                euclid=(5, 8, 0),
            ),
            LayerRecipe(
                id="drums",
                kind="sample",
                patterns=(
                    "bd*4, [~ sd]*2, hh*16",
                    "bd(5,8), sd*2, hh*16, cp(3,8)",
                    "bd*6, [sd cp]*4, hh*16",
                ),
                sound="",
                gain=0.48,
                follow_filter=False,
                hpf=40,
                release=0.16,
                room=0.06,
                shape=0.14,
                distort=0.34,
            ),
            LayerRecipe(
                id="edge",
                kind="note",
                patterns=("{note}", "{note}", "{note}"),
                sound="square",
                note_offset=7,
                gain=0.13,
                lpf_ratio=1.18,
                hpf=350,
                release=0.14,
                shape=0.52,
                distort=0.85,
                crush=5,
                pan="<0 1>",
                euclid=(7, 16, 3),
            ),
        ),
        mode_actions=("none", "stutter", "fast"),
        mode_amounts=(1.0, 1.8, 1.22),
        mode_layer_gain=0.26,
        gesture=GestureRecipe(
            pinch_gain=1.28,
            pinch_lpf_offset=1200,
            pinch_fast=1.12,
            pinch_shape=0.56,
            release_gain=0.88,
            release_room=0.10,
            release_delay=0.08,
            hold_layer=LayerRecipe(
                id="hold_pressure",
                kind="note",
                patterns=("{note}",) * 3,
                sound="sawtooth",
                note_offset=-12,
                gain=0.38,
                lpf_ratio=0.82,
                hpf=60,
                release=0.18,
                shape=0.68,
                distort=0.95,
                crush=5,
                euclid=(7, 8, 1),
            ),
            sweep_left="rev",
            sweep_right="fast",
            sweep_amount=1.35,
        ),
    ),
}

_MODE_INDEX = {
    "single": 0,
    "pulse": 1,
    "stutter": 2,
}


def get_scene(profile_id: str) -> SceneRecipe:
    return _SCENES.get(profile_id, _SCENES["neutral"])


def resolve_scene_payload(
    scene: SceneRecipe,
    pattern_mode: str,
) -> dict[str, object]:
    mode_index = _MODE_INDEX.get(pattern_mode, 0)
    payload = {
        "id": scene.id,
        "name": scene.name,
        "description": scene.description,
        "beats_per_cycle": scene.beats_per_cycle,
        "master_gain": scene.master_gain,
        "continuous_update_ms": scene.continuous_update_ms,
        "inactive_grace_ms": scene.inactive_grace_ms,
        "synth_change_priority": scene.synth_change_priority,
        "mode_action": scene.mode_actions[mode_index],
        "mode_amount": scene.mode_amounts[mode_index],
        "mode_layer_gain": scene.mode_layer_gain,
        "layers": [
            _resolve_layer_payload(layer, mode_index)
            for layer in scene.layers
        ],
        "gesture": asdict(scene.gesture),
    }
    payload["gesture"]["hold_layer"] = _resolve_layer_payload(
        scene.gesture.hold_layer,
        mode_index,
    )
    return payload


def scene_summary_payload(scene: SceneRecipe) -> dict[str, object]:
    return {
        "id": scene.id,
        "name": scene.name,
        "description": scene.description,
        "beats_per_cycle": scene.beats_per_cycle,
        "master_gain": scene.master_gain,
        "continuous_update_ms": scene.continuous_update_ms,
        "inactive_grace_ms": scene.inactive_grace_ms,
        "synth_change_priority": scene.synth_change_priority,
        "layers": tuple(layer.id for layer in scene.layers),
    }


def _resolve_layer_payload(
    layer: LayerRecipe,
    mode_index: int,
) -> dict[str, object]:
    payload = asdict(layer)
    payload["pattern"] = layer.patterns[mode_index]
    payload.pop("patterns")
    return payload
