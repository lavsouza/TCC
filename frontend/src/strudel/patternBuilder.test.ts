import { describe, expect, it } from "vitest";

import type { MusicalState } from "../api/contracts";
import { buildPatternCode } from "./patternBuilder";

const activeState = {
  active: true,
  strudel_note: "c4",
  gain: 0.4,
  lpf: 3200,
  synth: "triangle",
  gesture_phase: "idle",
  gesture_event: "none",
  sweep_direction: "none",
  pattern_mode: "single",
  selected_profile: "happy",
  profile_bpm: 120,
  profile_density: 1.18,
  profile_variation: 0.78,
  scene_beats_per_cycle: 4,
  scene: {
    beats_per_cycle: 4,
    master_gain: 1.45,
    mode_action: "palindrome",
    mode_amount: 1,
    mode_layer_gain: 0.18,
    layers: [
      {
        id: "melody",
        kind: "note",
        pattern: "{note} {note}",
        sound: "triangle",
        use_motion_synth: true,
        note_offset: 0,
        intervals: "",
        gain: 0.68,
        follow_filter: true,
        lpf_ratio: 1,
        hpf: 0,
        attack: 0,
        release: 0.18,
        room: 0.24,
        delay: 0,
        delay_time: 0,
        shape: 0,
        distort: 0,
        crush: 0,
        pan: "",
        fast: 1,
        slow: 1,
        euclid: null,
        palindrome: false,
      },
    ],
    gesture: {
      pinch_gain: 1.22,
      pinch_lpf_offset: 900,
      pinch_fast: 1.12,
      pinch_shape: 0.08,
      release_gain: 0.84,
      release_room: 0.42,
      release_delay: 0.18,
      hold_layer: null,
      sweep_left: "rev",
      sweep_right: "palindrome",
      sweep_amount: 1,
    },
  },
} as unknown as MusicalState;

describe("buildPatternCode", () => {
  it("compila tempo, cena e efeitos em sintaxe Strudel", () => {
    const code = buildPatternCode(activeState);

    expect(code).toContain("setcpm(120 / 4);");
    expect(code).toContain('note("c4 c4")');
    expect(code).toContain('.s("triangle")');
    expect(code).toContain(".postgain(1.45)");
    expect(code).toContain(".palindrome()");
  });

  it("gera hush para estado inativo", () => {
    const code = buildPatternCode({
      ...activeState,
      active: false,
    });

    expect(code).toBe("hush()");
  });

  it("aplica acento de pinch sem remover a cena", () => {
    const code = buildPatternCode({
      ...activeState,
      gesture_phase: "pinch",
      gesture_event: "pinch",
    });

    expect(code).toContain(".postgain(1.22)");
    expect(code).toContain(".lpf(4100)");
    expect(code).toContain(".shape(0.08)");
  });
});
