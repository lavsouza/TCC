let runtimeReady = false;
let socket = null;
let wsUrl = "";
let playbackArmed = false;
let latestState = null;

const statusText = document.getElementById("status-text");
const codeView = document.getElementById("code-view");
const connectButton = document.getElementById("connect-button");
const playButton = document.getElementById("play-button");
const stopButton = document.getElementById("stop-button");
const previewImage = document.getElementById("preview-image");
const previewPlaceholder = document.getElementById("preview-placeholder");

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
};

async function loadConfig() {
  const response = await fetch("./config.json");
  if (!response.ok) {
    throw new Error("Nao foi possivel carregar a configuracao local do Strudel.");
  }
  const config = await response.json();
  wsUrl = config.wsUrl;
  setStatus(`Pronto para conectar em ${wsUrl}`);
}

function setStatus(message) {
  statusText.textContent = message;
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
  return note(state.strudel_note).s(state.synth).gain(state.gain).lpf(state.lpf);
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

loadConfig().catch((error) => {
  setStatus(error.message);
});
