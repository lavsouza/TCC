from __future__ import annotations

from integration.strudel.models import StrudelState


def build_code(state: StrudelState) -> str:
    if not state.active:
        return "hush()"

    return (
        f'note("{state.strudel_note}")'
        f'.s("{state.synth}")'
        f".gain({state.gain})"
        f".lpf({state.lpf})"
    )
