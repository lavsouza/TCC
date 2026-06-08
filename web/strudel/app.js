let runtimeReady = false;
let strudelRepl = null;
let socket = null;
let wsUrl = "";
let playbackArmed = false;
let playbackActive = false;
let patternUpdateRunning = false;
let patternUpdateRequested = false;
let priorityUpdateRequested = false;
let patternUpdateTimer = null;
let inactiveStopTimer = null;
let targetPlaybackState = null;
let smoothedPlaybackState = null;
let lastStructureKey = "";
let lastPatternUpdateAt = 0;
let lastCyclesPerMinute = null;
let latestState = null;
let profileCatalog = new Map();
let selectedProfileId = "neutral";

const CONTINUOUS_UPDATE_MS = 150;
const PRIORITY_UPDATE_MS = 45;
const INACTIVE_GRACE_MS = 360;
const MIN_TRANSITION_SECONDS = 0.12;

const statusText = document.getElementById("status-text");
const codeView = document.getElementById("code-view");
const connectButton = document.getElementById("connect-button");
const playButton = document.getElementById("play-button");
const stopButton = document.getElementById("stop-button");
const previewImage = document.getElementById("preview-image");
const previewPlaceholder = document.getElementById("preview-placeholder");
const emotionSelect = document.getElementById("emotion-select");

const fields = {
  note: document.getElementById("note-value"),
  strudelNote: document.getElementById("strudel-note-value"),
  frequency: document.getElementById("frequency-value"),
  gain: document.getElementById("gain-value"),
  brightness: document.getElementById("brightness-value"),
  lpf: document.getElementById("lpf-value"),
  synth: document.getElementById("synth-value"),
  active: document.getElementById("active-value"),
  handsDetected: document.getElementById("hands-detected-value"),
  primaryHand: document.getElementById("primary-hand-value"),
  secondaryHand: document.getElementById("secondary-hand-value"),
  brightnessSource: document.getElementById("brightness-source-value"),
  gestureLabel: document.getElementById("gesture-label-value"),
  gestureEvent: document.getElementById("gesture-event-value"),
  gesturePhase: document.getElementById("gesture-phase-value"),
  patternMode: document.getElementById("pattern-mode-value"),
  sweepDirection: document.getElementById("sweep-direction-value"),
  profileName: document.getElementById("profile-name-value"),
  profileDescription: document.getElementById("profile-description-value"),
  emotion: document.getElementById("emotion-value"),
  emotionSource: document.getElementById("emotion-source-value"),
  emotionConfidence: document.getElementById("emotion-confidence-value"),
  profileBpm: document.getElementById("profile-bpm-value"),
  profileDensity: document.getElementById("profile-density-value"),
  profileIntensity: document.getElementById("profile-intensity-value"),
  profileVariation: document.getElementById("profile-variation-value"),
  sceneName: document.getElementById("scene-name-value"),
  sceneLayers: document.getElementById("scene-layers-value"),
};

function preventBrowserZoom(event) {
  event.preventDefault();
}

document.addEventListener("gesturestart", preventBrowserZoom, { passive: false });
document.addEventListener("gesturechange", preventBrowserZoom, { passive: false });
document.addEventListener("gestureend", preventBrowserZoom, { passive: false });
document.addEventListener(
  "wheel",
  (event) => {
    if (event.ctrlKey) {
      preventBrowserZoom(event);
    }
  },
  { passive: false },
);

async function loadConfig() {
  const response = await fetch("./config.json");
  if (!response.ok) {
    throw new Error("Nao foi possivel carregar a configuracao local do Strudel.");
  }

  const config = await response.json();
  wsUrl = config.wsUrl;
  setStatus(`Pronto para conectar em ${wsUrl}`);
  setupProfileCatalog(
    config.emotionProfiles || config.presets || [],
    config.defaultEmotionId || config.defaultPresetId || "neutral",
  );
}

function setupProfileCatalog(profiles, defaultProfileId) {
  profileCatalog = new Map();
  emotionSelect.innerHTML = "";

  profiles.forEach((profile) => {
    profileCatalog.set(profile.id, profile);
    const option = document.createElement("option");
    option.value = profile.id;
    option.textContent = profile.label || profile.name;
    emotionSelect.appendChild(option);
  });

  selectedProfileId = profileCatalog.has(defaultProfileId) ? defaultProfileId : "neutral";
  emotionSelect.value = selectedProfileId;
  renderProfileDetails(selectedProfileId);
}

function setStatus(message) {
  statusText.textContent = message;
}

function renderProfileDetails(profileId) {
  const profile = resolveProfile(profileId);
  fields.profileName.textContent = profile.label || profile.name;
  fields.profileDescription.textContent = profile.description;
  fields.emotion.textContent = profile.emotion || profile.id;
  fields.profileBpm.textContent = String(profile.bpm);
  fields.profileDensity.textContent = Number(profile.density).toFixed(3);
  fields.profileIntensity.textContent = Number(profile.intensity || 1).toFixed(3);
  fields.profileVariation.textContent = Number(profile.variation || 0).toFixed(3);
  fields.sceneName.textContent = profile.scene?.name || "Cena basica";
  fields.sceneLayers.textContent = (profile.scene?.layers || ["melody"]).join(", ");
}

function resolveProfile(profileId) {
  return profileCatalog.get(profileId) || profileCatalog.get("neutral") || {
    id: "neutral",
    emotion: "neutral",
    label: "Neutro",
    name: "Neutro",
    description: "Perfil padrao.",
    bpm: 92,
    density: 1,
    intensity: 1,
    variation: 0.3,
    rhythm_patterns: ["{note}"],
    synth_family: ["sawtooth"],
    scale_notes: ["C", "D#", "F", "G", "A#"],
  };
}

function renderState(state) {
  fields.note.textContent = state.note_label;
  fields.strudelNote.textContent = state.strudel_note;
  fields.frequency.textContent = `${state.frequency.toFixed(1)} Hz`;
  fields.gain.textContent = state.gain.toFixed(3);
  fields.brightness.textContent = state.brightness.toFixed(3);
  fields.lpf.textContent = String(state.lpf);
  fields.synth.textContent = state.synth;
  fields.active.textContent = state.active ? "sim" : "nao";
  fields.handsDetected.textContent = String(state.hands_detected);
  fields.primaryHand.textContent = state.primary_handedness;
  fields.secondaryHand.textContent = state.secondary_handedness;
  fields.brightnessSource.textContent = state.brightness_source;
  fields.gestureLabel.textContent = state.gesture_label;
  fields.gestureEvent.textContent = state.gesture_event;
  fields.gesturePhase.textContent = state.gesture_phase;
  fields.patternMode.textContent = state.pattern_mode;
  fields.sweepDirection.textContent = state.sweep_direction;
  selectedProfileId = state.selected_profile || state.selected_preset || selectedProfileId;
  emotionSelect.value = selectedProfileId;
  renderProfileDetails(selectedProfileId);
  fields.emotion.textContent = state.emotion || "neutral";
  fields.emotionSource.textContent = state.emotion_source || "manual";
  fields.emotionConfidence.textContent = Number(
    state.emotion_confidence ?? 1,
  ).toFixed(3);
  fields.profileBpm.textContent = String(state.profile_bpm ?? state.preset_bpm);
  fields.profileDensity.textContent = Number(
    state.profile_density ?? state.preset_density,
  ).toFixed(3);
  fields.profileIntensity.textContent = Number(
    state.profile_intensity ?? state.preset_gain_scale ?? 1,
  ).toFixed(3);
  fields.profileVariation.textContent = Number(
    state.profile_variation ?? 0,
  ).toFixed(3);
  fields.sceneName.textContent = state.scene_name || state.scene?.name || "Cena basica";
  fields.sceneLayers.textContent = (
    state.scene_layers
    || state.scene?.layers?.map((layer) => layer.id)
    || ["melody"]
  ).join(", ");
  codeView.textContent = buildPatternCode(state);
}

function renderPreview(frame) {
  previewImage.src = frame.image;
  previewImage.width = frame.width;
  previewImage.height = frame.height;
  previewImage.style.display = "block";
  previewPlaceholder.style.display = "none";
}

async function ensureRuntime() {
  if (runtimeReady) {
    return;
  }

  if (typeof initStrudel !== "function") {
    throw new Error("Runtime do Strudel nao foi carregado.");
  }

  setStatus("Carregando runtime e samples do Strudel...");
  strudelRepl = await Promise.resolve(initStrudel({
    prebake: () => samples("github:tidalcycles/dirt-samples"),
  }));
  if (typeof strudelRepl?.setPattern !== "function") {
    throw new Error("Runtime do Strudel nao oferece atualizacao continua de pattern.");
  }
  if (typeof strudelRepl?.setCps !== "function") {
    throw new Error("Runtime do Strudel nao oferece controle de tempo continuo.");
  }
  runtimeReady = true;
  setStatus("Runtime do Strudel pronto. Aguardando dados...");
}

function buildPatternCode(state) {
  return buildPatternExpression(state, false).code;
}

function buildPatternExpression(state, instantiate = false) {
  if (!state.active) {
    return createPatternExpression("hush()", null);
  }

  const base = state.scene?.layers?.length
    ? buildScenePatternExpression(state, instantiate)
    : buildLegacyBasePatternExpression(state, instantiate);
  const withMode = state.scene?.layers?.length
    ? applySceneMode(base, state)
    : applyPatternMode(base, state);
  const withGesture = applyGestureVariation(withMode, state, instantiate);
  const bpm = state.profile_bpm ?? state.preset_bpm ?? 92;
  const beatsPerCycle = state.scene_beats_per_cycle
    ?? state.scene?.beats_per_cycle
    ?? 4;

  return createPatternExpression(
    `setcpm(${formatCodeArg(bpm)} / ${formatCodeArg(Math.max(beatsPerCycle, 1))});\n\n${withGesture.code}`,
    withGesture.value,
  );
}

function buildScenePatternExpression(state, instantiate) {
  const layers = state.scene.layers.map((layer) => (
    buildSceneLayerExpression(layer, state, instantiate)
  ));
  let scenePattern = stackExpressions(layers, instantiate);
  const density = state.profile_density ?? state.preset_density ?? 1;
  if (density !== 1) {
    scenePattern = callPatternMethod(scenePattern, "fast", [density]);
  }
  const masterGain = Number(state.scene.master_gain ?? 1);
  if (masterGain !== 1) {
    scenePattern = callPatternMethod(scenePattern, "postgain", [masterGain]);
  }
  return scenePattern;
}

function buildSceneLayerExpression(layer, state, instantiate) {
  const patternText = String(layer.pattern || "{note}").replaceAll(
    "{note}",
    state.strudel_note,
  );
  let pattern;

  if (layer.kind === "sample") {
    pattern = createRootExpression(
      "s",
      [patternText],
      instantiate ? s(patternText) : null,
    );
  } else {
    pattern = createRootExpression(
      "note",
      [patternText],
      instantiate ? note(patternText) : null,
    );
    if (layer.note_offset) {
      pattern = callPatternMethod(pattern, "add", [layer.note_offset]);
    }
    if (layer.intervals) {
      pattern = callPatternMethod(pattern, "add", [layer.intervals]);
    }
    pattern = callPatternMethod(
      pattern,
      "s",
      [layer.use_motion_synth ? state.synth : layer.sound],
    );
  }

  pattern = callPatternMethod(pattern, "gain", [
    state.gain * Number(layer.gain ?? 1),
  ]);
  if (layer.follow_filter !== false) {
    pattern = callPatternMethod(pattern, "lpf", [
      clamp(state.lpf * Number(layer.lpf_ratio ?? 1), 100, 12000),
    ]);
  }

  pattern = applyNumberEffect(pattern, "hpf", layer.hpf);
  pattern = applyNumberEffect(pattern, "attack", layer.attack);
  pattern = applyNumberEffect(pattern, "release", layer.release);
  pattern = applyNumberEffect(pattern, "room", layer.room);
  pattern = applyNumberEffect(pattern, "delay", layer.delay);
  pattern = applyNumberEffect(pattern, "delaytime", layer.delay_time);
  pattern = applyNumberEffect(pattern, "shape", layer.shape);
  pattern = applyNumberEffect(pattern, "distort", layer.distort);
  pattern = applyNumberEffect(pattern, "crush", layer.crush);

  if (layer.pan) {
    pattern = callPatternMethod(pattern, "pan", [layer.pan]);
  }

  if (layer.euclid) {
    const [pulses, steps, rotation] = layer.euclid;
    pattern = rotation
      ? callPatternMethod(pattern, "euclidRot", [pulses, steps, rotation])
      : callPatternMethod(pattern, "euclid", [pulses, steps]);
  }

  if (Number(layer.fast ?? 1) !== 1) {
    pattern = callPatternMethod(pattern, "fast", [layer.fast]);
  }
  if (Number(layer.slow ?? 1) !== 1) {
    pattern = callPatternMethod(pattern, "slow", [layer.slow]);
  }
  if (layer.palindrome) {
    pattern = callPatternMethod(pattern, "palindrome");
  }

  return pattern;
}

function applyNumberEffect(pattern, method, value) {
  const numericValue = Number(value || 0);
  return numericValue ? callPatternMethod(pattern, method, [numericValue]) : pattern;
}

function buildLegacyBasePatternExpression(state, instantiate) {
  const rhythm = state.profile_rhythm || state.preset_rhythm || "{note}";
  const density = state.profile_density ?? state.preset_density ?? 1;
  const notePattern = rhythm.replaceAll("{note}", state.strudel_note);
  return callPatternMethod(
    callPatternMethod(
      callPatternMethod(
        callPatternMethod(
          createRootExpression(
            "note",
            [notePattern],
            instantiate ? note(notePattern) : null,
          ),
          "s",
          [state.synth],
        ),
        "gain",
        [state.gain],
      ),
      "lpf",
      [state.lpf],
    ),
    "fast",
    [density],
  );
}

function applySceneMode(pattern, state) {
  const action = state.scene.mode_action || "none";
  const amount = Number(state.scene.mode_amount ?? 1);

  if (action === "fast") {
    return callPatternMethod(pattern, "fast", [amount]);
  }
  if (action === "slow") {
    return callPatternMethod(pattern, "slow", [amount]);
  }
  if (action === "palindrome") {
    return callPatternMethod(pattern, "palindrome");
  }
  if (action === "stutter") {
    const layerGain = Number(state.scene.mode_layer_gain ?? 0.2);
    return stackExpressions([
      pattern,
      callPatternMethod(
        callPatternMethod(pattern, "fast", [amount]),
        "postgain",
        [layerGain],
      ),
    ]);
  }
  return pattern;
}

function applyPatternMode(pattern, state) {
  const variation = state.profile_variation ?? 0;
  if (state.pattern_mode === "pulse") {
    return callPatternMethod(pattern, "fast", [1 + 0.35 * variation]);
  }

  if (state.pattern_mode === "stutter") {
    const layerGain = Math.max(state.gain * (0.3 + 0.3 * variation), 0.03);
    return stackExpressions([
      pattern,
      callPatternMethod(
        callPatternMethod(pattern, "fast", [2]),
        "gain",
        [layerGain],
      ),
    ]);
  }

  return pattern;
}

function applyGestureVariation(pattern, state, instantiate) {
  if (state.scene?.gesture) {
    return applySceneGestureVariation(pattern, state, instantiate);
  }

  if (state.gesture_phase === "hold") {
    const layerGain = Math.max(state.gain * 0.42, 0.03);
    return stackExpressions([
      pattern,
      callPatternMethod(
        callPatternMethod(pattern, "fast", [2]),
        "gain",
        [layerGain],
      ),
    ]);
  }

  if (state.gesture_phase === "pinch" || state.gesture_event === "pinch") {
    const accentGain = Math.min(state.gain * 1.22, 1);
    const accentLpf = Math.min(state.lpf + 450, 9000);
    return callPatternMethod(
      callPatternMethod(pattern, "gain", [accentGain]),
      "lpf",
      [accentLpf],
    );
  }

  if (state.gesture_event === "release") {
    const releaseGain = Math.max(state.gain * 0.65, 0.02);
    return callPatternMethod(pattern, "gain", [releaseGain]);
  }

  return pattern;
}

function applySceneGestureVariation(pattern, state, instantiate) {
  const gesture = state.scene.gesture;

  if (state.gesture_phase === "hold" && gesture.hold_layer) {
    pattern = stackExpressions([
      pattern,
      buildSceneLayerExpression(gesture.hold_layer, state, instantiate),
    ]);
  }

  if (state.gesture_phase === "pinch" || state.gesture_event === "pinch") {
    pattern = callPatternMethod(
      callPatternMethod(pattern, "postgain", [Number(gesture.pinch_gain ?? 1)]),
      "lpf",
      [Math.min(state.lpf + Number(gesture.pinch_lpf_offset ?? 0), 12000)],
    );
    if (Number(gesture.pinch_fast ?? 1) !== 1) {
      pattern = callPatternMethod(pattern, "fast", [gesture.pinch_fast]);
    }
    if (Number(gesture.pinch_shape ?? 0)) {
      pattern = callPatternMethod(pattern, "shape", [gesture.pinch_shape]);
    }
  }

  if (state.gesture_event === "release") {
    pattern = callPatternMethod(
      callPatternMethod(pattern, "postgain", [Number(gesture.release_gain ?? 0.75)]),
      "room",
      [Number(gesture.release_room ?? 0)],
    );
    if (Number(gesture.release_delay ?? 0)) {
      pattern = callPatternMethod(pattern, "delay", [gesture.release_delay]);
    }
  }

  if (state.gesture_event === "sweep") {
    const action = state.sweep_direction === "left"
      ? gesture.sweep_left
      : gesture.sweep_right;
    pattern = applyDirectionalAction(
      pattern,
      action,
      Number(gesture.sweep_amount ?? 1),
    );
  }

  return pattern;
}

function applyDirectionalAction(pattern, action, amount) {
  if (action === "rev") {
    return callPatternMethod(pattern, "rev");
  }
  if (action === "palindrome") {
    return callPatternMethod(pattern, "palindrome");
  }
  if (action === "fast") {
    return callPatternMethod(pattern, "fast", [amount]);
  }
  if (action === "slow") {
    return callPatternMethod(pattern, "slow", [amount]);
  }
  return pattern;
}

function createPatternExpression(code, value) {
  return { code, value };
}

function createRootExpression(functionName, args, value) {
  return createPatternExpression(
    `${functionName}(${args.map(formatCodeArg).join(", ")})`,
    value,
  );
}

function callPatternMethod(pattern, method, args = []) {
  const code = `(${pattern.code}).${method}(${args.map(formatCodeArg).join(", ")})`;
  const value = pattern.value === null
    ? null
    : pattern.value[method](...args);
  return createPatternExpression(code, value);
}

function stackExpressions(patterns) {
  const canInstantiate = patterns.every((pattern) => pattern.value !== null);
  const code = `stack(\n  ${patterns.map((pattern) => indentCode(pattern.code)).join(",\n  ")}\n)`;
  return createPatternExpression(
    code,
    canInstantiate ? stack(...patterns.map((pattern) => pattern.value)) : null,
  );
}

function indentCode(code) {
  return code.replaceAll("\n", "\n  ");
}

function formatCodeArg(value) {
  if (typeof value === "number") {
    return String(Number(value.toFixed(6)));
  }
  return JSON.stringify(value);
}

function clamp(value, minimum, maximum) {
  return Math.max(minimum, Math.min(maximum, value));
}

function applyState(state) {
  latestState = state;
  renderState(state);

  if (!runtimeReady || !playbackArmed) {
    return;
  }

  if (!state.active) {
    scheduleInactiveStop(state);
    return;
  }

  cancelInactiveStop();
  targetPlaybackState = state;
  const structureKey = buildStructureKey(state);
  const priority = structureKey !== lastStructureKey;
  lastStructureKey = structureKey;
  requestPatternUpdate(priority);
}

function buildStructureKey(state) {
  const synthKey = state.scene?.synth_change_priority === false
    ? "continuous-synth"
    : state.synth;
  return [
    state.selected_profile || state.selected_preset,
    state.pattern_mode,
    state.gesture_phase,
    state.gesture_event,
    state.sweep_direction,
    synthKey,
  ].join("|");
}

function requestPatternUpdate(priority = false) {
  patternUpdateRequested = true;
  priorityUpdateRequested ||= priority;

  if (patternUpdateRunning) {
    return;
  }

  const minimumInterval = priorityUpdateRequested
    ? PRIORITY_UPDATE_MS
    : getContinuousUpdateMs(targetPlaybackState);
  const elapsed = performance.now() - lastPatternUpdateAt;
  const delay = Math.max(0, minimumInterval - elapsed);

  if (patternUpdateTimer !== null) {
    if (!priority) {
      return;
    }
    clearTimeout(patternUpdateTimer);
  }

  patternUpdateTimer = setTimeout(() => {
    patternUpdateTimer = null;
    void flushPatternUpdates();
  }, delay);
}

async function flushPatternUpdates() {
  patternUpdateRunning = true;

  try {
    patternUpdateRequested = false;
    priorityUpdateRequested = false;
    const targetState = targetPlaybackState;

    if (!runtimeReady || !playbackArmed || targetState === null) {
      return;
    }

    const state = smoothPlaybackState(targetState);

    const bpm = state.profile_bpm ?? state.preset_bpm ?? 92;
    const beatsPerCycle = state.scene_beats_per_cycle
      ?? state.scene?.beats_per_cycle
      ?? 4;
    const cyclesPerMinute = bpm / Math.max(beatsPerCycle, 1);

    if (cyclesPerMinute !== lastCyclesPerMinute) {
      strudelRepl.setCps(cyclesPerMinute / 60);
      lastCyclesPerMinute = cyclesPerMinute;
    }

    // setPattern replaces the musical function without resetting scheduler time.
    const expression = buildPatternExpression(state, true);
    codeView.textContent = expression.code;
    await strudelRepl.setPattern(expression.value, true);
    if (!playbackArmed) {
      stopScheduler(true);
      return;
    }
    playbackActive = true;
    lastPatternUpdateAt = performance.now();
  } catch (error) {
    setStatus(`Erro ao atualizar pattern Strudel: ${error.message}`);
  } finally {
    patternUpdateRunning = false;
    if (patternUpdateRequested) {
      requestPatternUpdate(priorityUpdateRequested);
    }
  }
}

function smoothPlaybackState(target) {
  if (smoothedPlaybackState === null) {
    smoothedPlaybackState = { ...target };
    return smoothedPlaybackState;
  }

  const elapsedSeconds = Math.max(
    (performance.now() - lastPatternUpdateAt) / 1000,
    getContinuousUpdateMs(target) / 1000,
  );
  const transitionSeconds = Math.max(
    Number(target.profile_transition_seconds ?? MIN_TRANSITION_SECONDS),
    MIN_TRANSITION_SECONDS,
  );
  const alpha = 1 - Math.exp(-elapsedSeconds / transitionSeconds);

  smoothedPlaybackState = {
    ...target,
    gain: interpolate(smoothedPlaybackState.gain, target.gain, alpha),
    lpf: Math.round(interpolate(smoothedPlaybackState.lpf, target.lpf, alpha)),
    brightness: interpolate(
      smoothedPlaybackState.brightness,
      target.brightness,
      alpha,
    ),
  };
  return smoothedPlaybackState;
}

function interpolate(current, target, alpha) {
  return current + (target - current) * alpha;
}

function getContinuousUpdateMs(state) {
  return Math.max(
    Number(state?.scene?.continuous_update_ms ?? CONTINUOUS_UPDATE_MS),
    PRIORITY_UPDATE_MS,
  );
}

function scheduleInactiveStop(state) {
  if (inactiveStopTimer !== null || !playbackActive) {
    return;
  }

  const graceMs = Math.max(
    Number(state?.scene?.inactive_grace_ms ?? INACTIVE_GRACE_MS),
    INACTIVE_GRACE_MS,
  );
  inactiveStopTimer = setTimeout(() => {
    inactiveStopTimer = null;
    targetPlaybackState = null;
    smoothedPlaybackState = null;
    lastStructureKey = "";
    stopScheduler();
  }, graceMs);
}

function cancelInactiveStop() {
  if (inactiveStopTimer === null) {
    return;
  }
  clearTimeout(inactiveStopTimer);
  inactiveStopTimer = null;
}

function stopScheduler(force = false) {
  if ((!playbackActive && !force) || strudelRepl === null) {
    return;
  }

  strudelRepl.stop();
  playbackActive = false;
  smoothedPlaybackState = null;
  lastCyclesPerMinute = null;
}

function handlePayload(payload) {
  if (payload.type === "state") {
    applyState(payload);
    return;
  }

  if (payload.type === "frame") {
    renderPreview(payload);
  }
}

function connectSocket() {
  if (socket !== null || !wsUrl) {
    return;
  }

  socket = new WebSocket(wsUrl);
  setStatus("Conectando ao servidor do Python...");

  socket.addEventListener("open", () => {
    setStatus("Conectado ao servidor do Python.");
    connectButton.disabled = true;
    sendEmotionSelection(selectedProfileId);
  });

  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    handlePayload(payload);
  });

  socket.addEventListener("close", () => {
    socket = null;
    connectButton.disabled = false;
    setStatus("Conexao encerrada. Clique em Conectar para tentar novamente.");
  });

  socket.addEventListener("error", () => {
    setStatus("Erro na conexao WebSocket com o Python.");
  });
}

function sendEmotionSelection(profileId) {
  if (socket === null || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  socket.send(JSON.stringify({
    type: "emotion/select",
    emotionId: profileId,
  }));
}

connectButton.addEventListener("click", () => {
  connectSocket();
});

playButton.addEventListener("click", async () => {
  try {
    await ensureRuntime();
    playbackArmed = true;
    setStatus("Audio do Strudel ativado.");
    if (latestState?.active) {
      targetPlaybackState = latestState;
      lastStructureKey = buildStructureKey(latestState);
      requestPatternUpdate(true);
    }
  } catch (error) {
    setStatus(error.message);
  }
});

stopButton.addEventListener("click", () => {
  playbackArmed = false;
  patternUpdateRequested = false;
  priorityUpdateRequested = false;
  cancelInactiveStop();
  if (patternUpdateTimer !== null) {
    clearTimeout(patternUpdateTimer);
    patternUpdateTimer = null;
  }
  stopScheduler(true);
  setStatus("Audio do Strudel parado.");
});

emotionSelect.addEventListener("change", (event) => {
  selectedProfileId = event.target.value;
  renderProfileDetails(selectedProfileId);
  sendEmotionSelection(selectedProfileId);
});

loadConfig().catch((error) => {
  setStatus(error.message);
});
