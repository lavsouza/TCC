import {
  useEffect,
  useRef,
  useState,
} from "react";

import { MoveCodeBeatsApi } from "./api/client";
import type {
  EmotionProfile,
  ErrorEvent,
  EventEnvelope,
  MusicalState,
  PreviewFrame,
  Session,
} from "./api/contracts";
import { StrudelEngine } from "./strudel/engine";

const EMPTY_CODE = "// Aguardando o primeiro estado musical...";

export default function App() {
  const apiRef = useRef(new MoveCodeBeatsApi());
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState("Preparando sessao...");
  const [connection, setConnection] = useState<"connecting" | "online" | "offline">(
    "connecting",
  );
  const [session, setSession] = useState<Session | null>(null);
  const [profiles, setProfiles] = useState<EmotionProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState("neutral");
  const [musicalState, setMusicalState] = useState<MusicalState | null>(null);
  const [preview, setPreview] = useState<PreviewFrame | null>(null);
  const [code, setCode] = useState(EMPTY_CODE);
  const [connectAttempt, setConnectAttempt] = useState(0);
  const engineRef = useRef<StrudelEngine | null>(null);

  if (engineRef.current === null) {
    engineRef.current = new StrudelEngine(setStatus, setCode);
  }

  useEffect(() => {
    let cancelled = false;
    let socket: WebSocket | null = null;
    const api = apiRef.current;

    async function connect() {
      setConnection("connecting");
      setStatus("Criando sessao com o backend...");
      try {
        const [catalog, createdSession] = await Promise.all([
          api.getCatalog(),
          api.createSession(),
        ]);
        if (cancelled) {
          return;
        }

        setProfiles(catalog.profiles);
        setSession(createdSession);
        setSelectedProfile(createdSession.selected_profile);
        socket = api.openStream(
          createdSession.id,
          handleEvent,
          (socketStatus) => {
            if (cancelled) {
              return;
            }
            if (socketStatus === "open") {
              setConnection("online");
              setStatus("Captura conectada. Ative o audio quando estiver pronto.");
              return;
            }
            setConnection("offline");
            setStatus(
              socketStatus === "error"
                ? "Falha na conexao em tempo real."
                : "Conexao com o backend encerrada.",
            );
          },
        );
        socketRef.current = socket;
      } catch (error) {
        if (cancelled) {
          return;
        }
        setConnection("offline");
        setStatus(errorMessage(error));
      }
    }

    function handleEvent(event: EventEnvelope) {
      if (event.type === "music.state.v1") {
        const state = event.data as unknown as MusicalState;
        setMusicalState(state);
        setSelectedProfile(state.selected_profile || "neutral");
        engineRef.current?.update(state);
        return;
      }
      if (event.type === "preview.frame.v1") {
        setPreview(event.data as unknown as PreviewFrame);
        return;
      }
      if (event.type === "runtime.status.v1") {
        const runtimeStatus = String(event.data.status ?? "unknown");
        if (runtimeStatus === "error") {
          setStatus("A camera nao pode ser iniciada. Consulte a API de saude.");
        }
        return;
      }
      if (event.type === "error.v1") {
        const problem = event.data as unknown as ErrorEvent;
        setStatus(problem.detail);
      }
    }

    void connect();
    return () => {
      cancelled = true;
      socket?.close();
      if (socketRef.current === socket) {
        socketRef.current = null;
      }
    };
  }, [connectAttempt]);

  useEffect(() => {
    const preventZoom = (event: Event) => event.preventDefault();
    const preventControlWheel = (event: WheelEvent) => {
      if (event.ctrlKey) {
        event.preventDefault();
      }
    };
    document.addEventListener("gesturestart", preventZoom, { passive: false });
    document.addEventListener("gesturechange", preventZoom, { passive: false });
    document.addEventListener("gestureend", preventZoom, { passive: false });
    document.addEventListener("wheel", preventControlWheel, { passive: false });
    return () => {
      document.removeEventListener("gesturestart", preventZoom);
      document.removeEventListener("gesturechange", preventZoom);
      document.removeEventListener("gestureend", preventZoom);
      document.removeEventListener("wheel", preventControlWheel);
    };
  }, []);

  useEffect(() => () => engineRef.current?.dispose(), []);

  const activeProfile = profiles.find((profile) => profile.id === selectedProfile)
    ?? profiles[0];

  async function changeProfile(profileId: string) {
    setSelectedProfile(profileId);
    if (!session) {
      return;
    }
    try {
      const updated = await apiRef.current.selectProfile(session.id, profileId);
      setSession(updated);
      setStatus(`Perfil ${profileLabel(profiles, profileId)} selecionado.`);
    } catch (error) {
      setSelectedProfile(session.selected_profile);
      setStatus(errorMessage(error));
    }
  }

  async function activateAudio() {
    try {
      await engineRef.current?.activate();
    } catch (error) {
      setStatus(errorMessage(error));
    }
  }

  return (
    <main className="app-shell">
      <header className="masthead">
        <div>
          <p className="kicker">Movimento em codigo. Codigo em som.</p>
          <h1>MoveCodeBeats</h1>
        </div>
        <div className={`connection-pill ${connection}`}>
          <span aria-hidden="true" />
          {connection === "online"
            ? "API conectada"
            : connection === "connecting"
              ? "Conectando"
              : "Desconectada"}
        </div>
      </header>

      <section className="control-deck">
        <div className="control-copy">
          <p className="section-index">01 / PERFORMANCE</p>
          <h2>Seu corpo conduz a cena.</h2>
          <p>{status}</p>
        </div>
        <div className="transport" aria-label="Controles de transporte">
          <button className="primary-action" type="button" onClick={activateAudio}>
            Ativar audio
          </button>
          <button type="button" onClick={() => engineRef.current?.stop()}>
            Parar
          </button>
          {connection === "offline" && (
            <button type="button" onClick={() => setConnectAttempt((value) => value + 1)}>
              Reconectar
            </button>
          )}
        </div>
        <label className="profile-control">
          <span>Perfil expressivo</span>
          <select
            value={selectedProfile}
            onChange={(event) => void changeProfile(event.target.value)}
            disabled={!profiles.length}
          >
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.label}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="performance-grid">
        <div className="visual-column">
          <article className="camera-card">
            <div className="card-heading">
              <div>
                <p className="section-index">02 / VISAO</p>
                <h2>Captura gestual</h2>
              </div>
              <span className="live-tag">MediaPipe</span>
            </div>
            <div className={`camera-viewport ${preview ? "has-feed" : ""}`}>
              {preview ? (
                <img
                  src={preview.image}
                  width={preview.width}
                  height={preview.height}
                  alt="Mãos detectadas pela câmera"
                  draggable={false}
                />
              ) : (
                <div className="camera-idle" aria-label="Aguardando camera">
                  <i />
                  <i />
                  <i />
                </div>
              )}
            </div>
          </article>

          <article className="code-card">
            <div className="card-heading">
              <div>
                <p className="section-index">03 / STRUDEL</p>
                <h2>Pattern executado</h2>
              </div>
              <span className="live-tag code-tag">TypeScript</span>
            </div>
            <pre><code>{code}</code></pre>
          </article>
        </div>

        <aside className="inspector">
          <div className="card-heading">
            <div>
              <p className="section-index">04 / ESTADO</p>
              <h2>Leitura musical</h2>
            </div>
            <span className={`gesture-orb ${musicalState?.active ? "active" : ""}`} />
          </div>

          <div className="hero-metric">
            <span>Nota atual</span>
            <strong>{musicalState?.note_label ?? "--"}</strong>
            <small>
              {musicalState ? `${musicalState.frequency.toFixed(1)} Hz` : "sem deteccao"}
            </small>
          </div>

          <dl className="metric-grid">
            <Metric label="Gain" value={fixed(musicalState?.gain)} />
            <Metric label="Brilho" value={fixed(musicalState?.brightness)} />
            <Metric label="Filtro LPF" value={musicalState?.lpf ?? 0} />
            <Metric label="Synth" value={musicalState?.synth ?? "sawtooth"} />
            <Metric label="Gesto" value={musicalState?.gesture_label ?? "idle"} />
            <Metric label="Pattern" value={musicalState?.pattern_mode ?? "single"} />
            <Metric label="Maos" value={musicalState?.hands_detected ?? 0} />
            <Metric
              label="Controle timbrico"
              value={musicalState?.brightness_source ?? "none"}
            />
          </dl>

          <div className="profile-story">
            <span className="profile-number">
              {String(profiles.findIndex((profile) => profile.id === selectedProfile) + 1)
                .padStart(2, "0")}
            </span>
            <div>
              <p>{activeProfile?.label ?? "Neutro"}</p>
              <h3>{musicalState?.scene_name ?? activeProfile?.scene?.name ?? "Pulso equilibrado"}</h3>
              <small>{activeProfile?.description ?? "Perfil musical padrao."}</small>
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function fixed(value: number | undefined): string {
  return (value ?? 0).toFixed(3);
}

function profileLabel(profiles: EmotionProfile[], profileId: string): string {
  return profiles.find((profile) => profile.id === profileId)?.label ?? profileId;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
