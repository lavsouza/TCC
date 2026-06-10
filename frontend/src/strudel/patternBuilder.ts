import type {
  LayerRecipe,
  MusicalState,
} from "../api/contracts";

export interface PatternLike {
  [method: string]: (...args: unknown[]) => PatternLike;
}

export interface PatternRuntime {
  note(pattern: string): PatternLike;
  s(pattern: string): PatternLike;
  stack(...patterns: PatternLike[]): PatternLike;
}

export interface PatternExpression {
  code: string;
  value: PatternLike | null;
}

export function buildPatternCode(state: MusicalState): string {
  return buildPatternExpression(state).code;
}

export function buildPatternExpression(
  state: MusicalState,
  runtime: PatternRuntime | null = null,
): PatternExpression {
  if (!state.active) {
    return expression("hush()", null);
  }

  const base = state.scene?.layers?.length
    ? buildScenePattern(state, runtime)
    : buildLegacyPattern(state, runtime);
  const withMode = state.scene?.layers?.length
    ? applySceneMode(base, state, runtime)
    : applyPatternMode(base, state, runtime);
  const withGesture = applyGesture(withMode, state, runtime);
  const bpm = state.profile_bpm ?? state.preset_bpm ?? 92;
  const beatsPerCycle = state.scene_beats_per_cycle
    ?? state.scene?.beats_per_cycle
    ?? 4;

  return expression(
    `setcpm(${formatArg(bpm)} / ${formatArg(Math.max(beatsPerCycle, 1))});\n\n${withGesture.code}`,
    withGesture.value,
  );
}

function buildScenePattern(
  state: MusicalState,
  runtime: PatternRuntime | null,
): PatternExpression {
  const layers = state.scene.layers.map((layer) => (
    buildLayer(layer, state, runtime)
  ));
  let pattern = stackExpressions(layers, runtime);
  const density = state.profile_density ?? state.preset_density ?? 1;
  if (density !== 1) {
    pattern = call(pattern, "fast", [density]);
  }

  const masterGain = Number(state.scene.master_gain ?? 1);
  if (masterGain !== 1) {
    pattern = call(pattern, "postgain", [masterGain]);
  }
  return pattern;
}

function buildLayer(
  layer: LayerRecipe,
  state: MusicalState,
  runtime: PatternRuntime | null,
): PatternExpression {
  const patternText = String(layer.pattern || "{note}").replaceAll(
    "{note}",
    state.strudel_note,
  );
  let pattern: PatternExpression;

  if (layer.kind === "sample") {
    pattern = root(
      "s",
      [patternText],
      runtime ? runtime.s(patternText) : null,
    );
  } else {
    pattern = root(
      "note",
      [patternText],
      runtime ? runtime.note(patternText) : null,
    );
    if (layer.note_offset) {
      pattern = call(pattern, "add", [layer.note_offset]);
    }
    if (layer.intervals) {
      pattern = call(pattern, "add", [layer.intervals]);
    }
    pattern = call(pattern, "s", [
      layer.use_motion_synth ? state.synth : layer.sound,
    ]);
  }

  pattern = call(pattern, "gain", [
    state.gain * Number(layer.gain ?? 1),
  ]);
  if (layer.follow_filter !== false) {
    pattern = call(pattern, "lpf", [
      clamp(state.lpf * Number(layer.lpf_ratio ?? 1), 100, 12000),
    ]);
  }

  pattern = numberEffect(pattern, "hpf", layer.hpf);
  pattern = numberEffect(pattern, "attack", layer.attack);
  pattern = numberEffect(pattern, "release", layer.release);
  pattern = numberEffect(pattern, "room", layer.room);
  pattern = numberEffect(pattern, "delay", layer.delay);
  pattern = numberEffect(pattern, "delaytime", layer.delay_time);
  pattern = numberEffect(pattern, "shape", layer.shape);
  pattern = numberEffect(pattern, "distort", layer.distort);
  pattern = numberEffect(pattern, "crush", layer.crush);

  if (layer.pan) {
    pattern = call(pattern, "pan", [layer.pan]);
  }
  if (layer.euclid) {
    const [pulses, steps, rotation] = layer.euclid;
    pattern = rotation
      ? call(pattern, "euclidRot", [pulses, steps, rotation])
      : call(pattern, "euclid", [pulses, steps]);
  }
  if (Number(layer.fast ?? 1) !== 1) {
    pattern = call(pattern, "fast", [layer.fast]);
  }
  if (Number(layer.slow ?? 1) !== 1) {
    pattern = call(pattern, "slow", [layer.slow]);
  }
  if (layer.palindrome) {
    pattern = call(pattern, "palindrome");
  }
  return pattern;
}

function buildLegacyPattern(
  state: MusicalState,
  runtime: PatternRuntime | null,
): PatternExpression {
  const rhythm = state.profile_rhythm || state.preset_rhythm || "{note}";
  const density = state.profile_density ?? state.preset_density ?? 1;
  const notePattern = rhythm.replaceAll("{note}", state.strudel_note);
  let pattern = root(
    "note",
    [notePattern],
    runtime ? runtime.note(notePattern) : null,
  );
  pattern = call(pattern, "s", [state.synth]);
  pattern = call(pattern, "gain", [state.gain]);
  pattern = call(pattern, "lpf", [state.lpf]);
  return call(pattern, "fast", [density]);
}

function applySceneMode(
  pattern: PatternExpression,
  state: MusicalState,
  runtime: PatternRuntime | null,
): PatternExpression {
  const action = state.scene.mode_action || "none";
  const amount = Number(state.scene.mode_amount ?? 1);

  if (action === "fast") {
    return call(pattern, "fast", [amount]);
  }
  if (action === "slow") {
    return call(pattern, "slow", [amount]);
  }
  if (action === "palindrome") {
    return call(pattern, "palindrome");
  }
  if (action === "stutter") {
    const layerGain = Number(state.scene.mode_layer_gain ?? 0.2);
    return stackExpressions([
      pattern,
      call(call(pattern, "fast", [amount]), "postgain", [layerGain]),
    ], runtime);
  }
  return pattern;
}

function applyPatternMode(
  pattern: PatternExpression,
  state: MusicalState,
  runtime: PatternRuntime | null,
): PatternExpression {
  const variation = state.profile_variation ?? 0;
  if (state.pattern_mode === "pulse") {
    return call(pattern, "fast", [1 + 0.35 * variation]);
  }
  if (state.pattern_mode === "stutter") {
    const layerGain = Math.max(state.gain * (0.3 + 0.3 * variation), 0.03);
    return stackExpressions([
      pattern,
      call(call(pattern, "fast", [2]), "gain", [layerGain]),
    ], runtime);
  }
  return pattern;
}

function applyGesture(
  pattern: PatternExpression,
  state: MusicalState,
  runtime: PatternRuntime | null,
): PatternExpression {
  const gesture = state.scene?.gesture;
  if (!gesture) {
    return pattern;
  }

  if (state.gesture_phase === "hold" && gesture.hold_layer) {
    pattern = stackExpressions([
      pattern,
      buildLayer(gesture.hold_layer, state, runtime),
    ], runtime);
  }

  if (state.gesture_phase === "pinch" || state.gesture_event === "pinch") {
    pattern = call(
      call(pattern, "postgain", [Number(gesture.pinch_gain ?? 1)]),
      "lpf",
      [Math.min(state.lpf + Number(gesture.pinch_lpf_offset ?? 0), 12000)],
    );
    if (Number(gesture.pinch_fast ?? 1) !== 1) {
      pattern = call(pattern, "fast", [gesture.pinch_fast]);
    }
    if (Number(gesture.pinch_shape ?? 0)) {
      pattern = call(pattern, "shape", [gesture.pinch_shape]);
    }
  }

  if (state.gesture_event === "release") {
    pattern = call(
      call(pattern, "postgain", [Number(gesture.release_gain ?? 0.75)]),
      "room",
      [Number(gesture.release_room ?? 0)],
    );
    if (Number(gesture.release_delay ?? 0)) {
      pattern = call(pattern, "delay", [gesture.release_delay]);
    }
  }

  if (state.gesture_event === "sweep") {
    const action = state.sweep_direction === "left"
      ? gesture.sweep_left
      : gesture.sweep_right;
    pattern = directionalAction(
      pattern,
      action,
      Number(gesture.sweep_amount ?? 1),
    );
  }
  return pattern;
}

function directionalAction(
  pattern: PatternExpression,
  action: string,
  amount: number,
): PatternExpression {
  if (action === "rev") {
    return call(pattern, "rev");
  }
  if (action === "palindrome") {
    return call(pattern, "palindrome");
  }
  if (action === "fast") {
    return call(pattern, "fast", [amount]);
  }
  if (action === "slow") {
    return call(pattern, "slow", [amount]);
  }
  return pattern;
}

function numberEffect(
  pattern: PatternExpression,
  method: string,
  value: number,
): PatternExpression {
  const numericValue = Number(value || 0);
  return numericValue ? call(pattern, method, [numericValue]) : pattern;
}

function root(
  functionName: string,
  args: unknown[],
  value: PatternLike | null,
): PatternExpression {
  return expression(
    `${functionName}(${args.map(formatArg).join(", ")})`,
    value,
  );
}

function call(
  pattern: PatternExpression,
  method: string,
  args: unknown[] = [],
): PatternExpression {
  const code = `(${pattern.code}).${method}(${args.map(formatArg).join(", ")})`;
  const value = pattern.value === null
    ? null
    : pattern.value[method](...args);
  return expression(code, value);
}

function stackExpressions(
  patterns: PatternExpression[],
  runtime: PatternRuntime | null,
): PatternExpression {
  const values = patterns.map((pattern) => pattern.value);
  const canInstantiate = runtime !== null && values.every((value) => value !== null);
  const code = `stack(\n  ${patterns.map((pattern) => indent(pattern.code)).join(",\n  ")}\n)`;
  return expression(
    code,
    canInstantiate
      ? runtime.stack(...values as PatternLike[])
      : null,
  );
}

function expression(
  code: string,
  value: PatternLike | null,
): PatternExpression {
  return { code, value };
}

function indent(code: string): string {
  return code.replaceAll("\n", "\n  ");
}

function formatArg(value: unknown): string {
  if (typeof value === "number") {
    return String(Number(value.toFixed(6)));
  }
  return JSON.stringify(value);
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}
