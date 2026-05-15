from __future__ import annotations

import re

NOTE_NAMES = {
    "C": "c",
    "C#": "c#",
    "D": "d",
    "D#": "d#",
    "E": "e",
    "F": "f",
    "F#": "f#",
    "G": "g",
    "G#": "g#",
    "A": "a",
    "A#": "a#",
    "B": "b",
    "Db": "db",
    "Eb": "eb",
    "Gb": "gb",
    "Ab": "ab",
    "Bb": "bb",
}

NOTE_PATTERN = re.compile(r"([A-G])([#b]?)(-?\d+)")


def to_strudel_note(note_label: str) -> str:
    if note_label in {"", "--", "~"}:
        return "~"

    match = NOTE_PATTERN.fullmatch(note_label)
    if match is None:
        raise ValueError(f"Nota invalida para Strudel: {note_label}")

    name = match.group(1) + match.group(2)
    octave = match.group(3)
    token = NOTE_NAMES.get(name)
    if token is None:
        raise ValueError(f"Nota invalida para Strudel: {note_label}")
    return f"{token}{octave}"
