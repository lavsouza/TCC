import type {
  Catalog,
  EventEnvelope,
  Session,
} from "./contracts";

const DEFAULT_API_URL = "http://127.0.0.1:8000";

export class MoveCodeBeatsApi {
  readonly baseUrl: string;

  constructor(baseUrl = import.meta.env.VITE_API_URL || DEFAULT_API_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async getCatalog(): Promise<Catalog> {
    return this.request<Catalog>("/api/v1/catalog");
  }

  async createSession(): Promise<Session> {
    return this.request<Session>("/api/v1/sessions", { method: "POST" });
  }

  async selectProfile(sessionId: string, profileId: string): Promise<Session> {
    return this.request<Session>(
      `/api/v1/sessions/${encodeURIComponent(sessionId)}/profile`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId }),
      },
    );
  }

  openStream(
    sessionId: string,
    onEvent: (event: EventEnvelope) => void,
    onStatus: (status: "open" | "closed" | "error") => void,
  ): WebSocket {
    const wsBase = this.baseUrl.replace(/^http/, "ws");
    const socket = new WebSocket(
      `${wsBase}/api/v1/sessions/${encodeURIComponent(sessionId)}/stream`,
    );
    socket.addEventListener("open", () => onStatus("open"));
    socket.addEventListener("close", () => onStatus("closed"));
    socket.addEventListener("error", () => onStatus("error"));
    socket.addEventListener("message", (message) => {
      onEvent(JSON.parse(message.data) as EventEnvelope);
    });
    return socket;
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, init);
    if (!response.ok) {
      const body = await response.json().catch(() => null) as {
        detail?: string;
      } | null;
      throw new Error(body?.detail || `Falha HTTP ${response.status}.`);
    }
    return response.json() as Promise<T>;
  }
}
