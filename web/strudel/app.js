let runtimeReady = false;
let socket = null;
let wsUrl = "";
let playbackArmed = false;
let latestState = null;
let presetCatalog = new Map();
let selectedPresetId = "neutral";

const statusText = document.getElementById("status-text");
const codeView = document.getElementById("code-view");
const connectButton = document.getElementById("connect-button");
const playButton = document.getElementById("play-button");
const stopButton = document.getElementById("stop-button");
const previewImage = document.getElementById("preview-image");
const previewPlaceholder = document.getElementById("preview-placeholder");
const presetSelect = document.getElementById("preset-select");

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
  presetName: document.getElementById("preset-name-value"),
  presetDescription: document.getElementById("preset-description-value"),
};

async function loadConfig() {
  const response = await fetch("./config.json");
  if (!response.ok) {
    throw new Error("Nao foi possivel carregar a configuracao local do Strudel.");
  }

  const config = await response.json();
  wsUrl = config.wsUrl;
  setStatus(`Pronto para conectar em ${wsUrl}`);
  setupPresetCatalog(config.presets || [], config.defaultPresetId || "neutral");
}

function setupPresetCatalog(presets, defaultPresetId) {
  presetCatalog = new Map();
  presetSelect.innerHTML = "";

  presets.forEach((preset) => {
    presetCatalog.set(preset.id, preset);
    const option = document.createElement("option");
    option.value = preset.id;
    option.textContent = preset.name;
    presetSelect.appendChild(option);
  });

  selectedPresetId = presetCatalog.has(defaultPresetId) ? defaultPresetId : "neutral";
  presetSelect.value = selectedPresetId;
  renderPresetDetails(selectedPresetId);
}

function setStatus(message) {
  statusText.textContent = message;
}

function renderPresetDetails(presetId) {
  const preset = resolvePreset(presetId);
  fields.presetName.textContent = preset.name;
  fields.presetDescription.textContent = preset.description;
}

function resolvePreset(presetId) {
  return presetCatalog.get(presetId) || presetCatalog.get("neutral") || {
    id: "neutral",
    name: "Neutral",
    description: "Preset padrao.",
    bpm: 92,
    rhythm_pattern: "{note}",
    default_synth: "sawtooth",
    scale_notes: ["C", "D#", "F", "G", "A#"],
    gain_scale: 1.0,
    filter_offset: 0,
    density: 1.0,
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
  selectedPresetId = state.selected_preset || selectedPresetId;
  presetSelect.value = selectedPresetId;
  renderPresetDetails(selectedPresetId);
  codeView.textContent = state.code;
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

  await Promise.resolve(initStrudel());
  runtimeReady = true;
  setStatus("Runtime do Strudel pronto. Aguardando dados...");
}

function buildPattern(state) {
  const base = buildBasePattern(state);
  const withMode = applyPatternMode(base, state);
  return applyGestureVariation(withMode, state);
}

function buildBasePattern(state) {
  const notePattern = state.preset_rhythm.replaceAll("{note}", state.strudel_note);
  const tempoFactor = Number(((state.preset_bpm / 92) * state.preset_density).toFixed(3));
  return note(notePattern)
    .s(state.synth)
    .gain(state.gain)
    .lpf(state.lpf)
    .fast(tempoFactor);
}

function applyPatternMode(pattern, state) {
  if (state.pattern_mode === "pulse") {
    return pattern.fast(1.35);
  }

  if (state.pattern_mode === "stutter") {
    const layerGain = Math.max(state.gain * 0.5, 0.03);
    return stack(pattern, pattern.fast(2).gain(layerGain));
  }

  return pattern;
}

function applyGestureVariation(pattern, state) {
  if (state.gesture_phase === "hold") {
    const layerGain = Math.max(state.gain * 0.42, 0.03);
    return stack(pattern, pattern.fast(2).gain(layerGain));
  }

  if (state.gesture_phase === "pinch" || state.gesture_event === "pinch") {
    const accentGain = Math.min(state.gain * 1.22, 1);
    const accentLpf = Math.min(state.lpf + 450, 9000);
    return pattern.gain(accentGain).lpf(accentLpf);
  }

  if (state.gesture_event === "release") {
    const releaseGain = Math.max(state.gain * 0.65, 0.02);
    return pattern.gain(releaseGain);
  }

  return pattern;
}

function applyState(state) {
  latestState = state;
  renderState(state);

  if (!runtimeReady || !playbackArmed) {
    return;
  }

  if (!state.active) {
    hush();
    return;
  }

  hush();
  buildPattern(state).play();
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
    sendPresetSelection(selectedPresetId);
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

function sendPresetSelection(presetId) {
  if (socket === null || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  socket.send(JSON.stringify({
    type: "preset/select",
    presetId,
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
    if (latestState !== null) {
      applyState(latestState);
    }
  } catch (error) {
    setStatus(error.message);
  }
});

stopButton.addEventListener("click", () => {
  playbackArmed = false;
  if (runtimeReady && typeof hush === "function") {
    hush();
  }
  setStatus("Audio do Strudel parado.");
});

presetSelect.addEventListener("change", (event) => {
  selectedPresetId = event.target.value;
  renderPresetDetails(selectedPresetId);
  sendPresetSelection(selectedPresetId);
});

loadConfig().catch((error) => {
  setStatus(error.message);
});
