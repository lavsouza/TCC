from __future__ import annotations

from integration.strudel.models import StrudelState


def build_code(state: StrudelState) -> str:
    if not state.active:
        return "hush()"

    base = _build_base_pattern(state)
    pattern_mode = _apply_pattern_mode(base, state)
    return _apply_gesture_variation(pattern_mode, state)


def _build_base_pattern(state: StrudelState) -> str:
    note_pattern = state.preset_rhythm.replace("{note}", state.strudel_note)
    tempo_factor = round((state.preset_bpm / 92.0) * state.preset_density, 3)
    return (
        f'note("{note_pattern}")'
        f'.s("{state.synth}")'
        f".gain({state.gain})"
        f".lpf({state.lpf})"
        f".fast({tempo_factor})"
    )


def _apply_pattern_mode(base: str, state: StrudelState) -> str:
    if state.pattern_mode == "pulse":
        return f"({base}).fast(1.35)"

    if state.pattern_mode == "stutter":
        layer_gain = round(max(state.gain * 0.5, 0.03), 3)
        return f"stack({base}, ({base}).fast(2).gain({layer_gain}))"

    return base


def _apply_gesture_variation(pattern: str, state: StrudelState) -> str:
    if state.gesture_phase == "hold":
        hold_gain = round(max(state.gain * 0.42, 0.03), 3)
        return f"stack({pattern}, ({pattern}).fast(2).gain({hold_gain}))"

    if state.gesture_phase == "pinch" or state.gesture_event == "pinch":
        accent_gain = round(min(state.gain * 1.22, 1.0), 3)
        accent_lpf = min(state.lpf + 450, 9000)
        return f"({pattern}).gain({accent_gain}).lpf({accent_lpf})"

    if state.gesture_event == "release":
        release_gain = round(max(state.gain * 0.65, 0.02), 3)
        return f"({pattern}).gain({release_gain})"

    return pattern
