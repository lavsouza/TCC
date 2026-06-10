import type { StrudelRepl } from "@strudel/web";

import type { MusicalState } from "../api/contracts";
import {
  buildPatternExpression,
  type PatternRuntime,
} from "./patternBuilder";

const CONTINUOUS_UPDATE_MS = 150;
const PRIORITY_UPDATE_MS = 45;
const INACTIVE_GRACE_MS = 360;
const MIN_TRANSITION_SECONDS = 0.12;

type StatusHandler = (message: string) => void;
type CodeHandler = (code: string) => void;

export class StrudelEngine {
  private repl: StrudelRepl | null = null;
  private runtimeReady = false;
  private playbackArmed = false;
  private playbackActive = false;
  private updateRunning = false;
  private updateRequested = false;
  private priorityRequested = false;
  private updateTimer: number | null = null;
  private inactiveTimer: number | null = null;
  private targetState: MusicalState | null = null;
  private smoothedState: MusicalState | null = null;
  private latestState: MusicalState | null = null;
  private lastStructureKey = "";
  private lastPatternUpdateAt = 0;
  private lastCyclesPerMinute: number | null = null;

  private patternRuntime: PatternRuntime | null = null;

  constructor(
    private readonly onStatus: StatusHandler,
    private readonly onCode: CodeHandler,
  ) {}

  async activate(): Promise<void> {
    if (!this.runtimeReady) {
      this.onStatus("Carregando runtime e samples do Strudel...");
      const {
        initStrudel,
        note,
        s,
        samples,
        stack,
      } = await import("@strudel/web");
      this.patternRuntime = { note, s, stack };
      this.repl = await Promise.resolve(initStrudel({
        prebake: () => samples("github:tidalcycles/dirt-samples"),
      }));
      if (
        typeof this.repl?.setPattern !== "function"
        || typeof this.repl?.setCps !== "function"
      ) {
        throw new Error("Runtime Strudel sem suporte ao scheduler continuo.");
      }
      this.runtimeReady = true;
    }

    this.playbackArmed = true;
    this.onStatus("Audio Strudel ativo.");
    if (this.latestState?.active) {
      this.targetState = this.latestState;
      this.lastStructureKey = this.structureKey(this.latestState);
      this.requestUpdate(true);
    }
  }

  update(state: MusicalState): void {
    this.latestState = state;
    this.onCode(buildPatternExpression(state).code);

    if (!this.runtimeReady || !this.playbackArmed) {
      return;
    }
    if (!state.active) {
      this.scheduleInactiveStop(state);
      return;
    }

    this.cancelInactiveStop();
    this.targetState = state;
    const structureKey = this.structureKey(state);
    const priority = structureKey !== this.lastStructureKey;
    this.lastStructureKey = structureKey;
    this.requestUpdate(priority);
  }

  stop(): void {
    this.playbackArmed = false;
    this.updateRequested = false;
    this.priorityRequested = false;
    this.cancelInactiveStop();
    if (this.updateTimer !== null) {
      window.clearTimeout(this.updateTimer);
      this.updateTimer = null;
    }
    this.stopScheduler(true);
    this.onStatus("Audio Strudel parado.");
  }

  dispose(): void {
    this.stop();
    this.repl = null;
    this.runtimeReady = false;
  }

  private structureKey(state: MusicalState): string {
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

  private requestUpdate(priority = false): void {
    this.updateRequested = true;
    this.priorityRequested ||= priority;
    if (this.updateRunning) {
      return;
    }

    const minimumInterval = this.priorityRequested
      ? PRIORITY_UPDATE_MS
      : this.continuousUpdateMs(this.targetState);
    const elapsed = performance.now() - this.lastPatternUpdateAt;
    const delay = Math.max(0, minimumInterval - elapsed);

    if (this.updateTimer !== null) {
      if (!priority) {
        return;
      }
      window.clearTimeout(this.updateTimer);
    }
    this.updateTimer = window.setTimeout(() => {
      this.updateTimer = null;
      void this.flushUpdates();
    }, delay);
  }

  private async flushUpdates(): Promise<void> {
    this.updateRunning = true;
    try {
      this.updateRequested = false;
      this.priorityRequested = false;
      const target = this.targetState;
      if (
        !this.repl
        || !this.patternRuntime
        || !this.playbackArmed
        || target === null
      ) {
        return;
      }

      const state = this.smooth(target);
      const bpm = state.profile_bpm ?? state.preset_bpm ?? 92;
      const beatsPerCycle = state.scene_beats_per_cycle
        ?? state.scene?.beats_per_cycle
        ?? 4;
      const cyclesPerMinute = bpm / Math.max(beatsPerCycle, 1);
      if (cyclesPerMinute !== this.lastCyclesPerMinute) {
        this.repl.setCps(cyclesPerMinute / 60);
        this.lastCyclesPerMinute = cyclesPerMinute;
      }

      const compiled = buildPatternExpression(state, this.patternRuntime);
      this.onCode(compiled.code);
      await this.repl.setPattern(compiled.value, true);
      if (!this.playbackArmed) {
        this.stopScheduler(true);
        return;
      }
      this.playbackActive = true;
      this.lastPatternUpdateAt = performance.now();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      this.onStatus(`Erro ao atualizar pattern Strudel: ${message}`);
    } finally {
      this.updateRunning = false;
      if (this.updateRequested) {
        this.requestUpdate(this.priorityRequested);
      }
    }
  }

  private smooth(target: MusicalState): MusicalState {
    if (this.smoothedState === null) {
      this.smoothedState = { ...target };
      return this.smoothedState;
    }

    const elapsedSeconds = Math.max(
      (performance.now() - this.lastPatternUpdateAt) / 1000,
      this.continuousUpdateMs(target) / 1000,
    );
    const transitionSeconds = Math.max(
      Number(target.profile_transition_seconds ?? MIN_TRANSITION_SECONDS),
      MIN_TRANSITION_SECONDS,
    );
    const alpha = 1 - Math.exp(-elapsedSeconds / transitionSeconds);

    this.smoothedState = {
      ...target,
      gain: interpolate(this.smoothedState.gain, target.gain, alpha),
      lpf: Math.round(interpolate(this.smoothedState.lpf, target.lpf, alpha)),
      brightness: interpolate(
        this.smoothedState.brightness,
        target.brightness,
        alpha,
      ),
    };
    return this.smoothedState;
  }

  private continuousUpdateMs(state: MusicalState | null): number {
    return Math.max(
      Number(state?.scene?.continuous_update_ms ?? CONTINUOUS_UPDATE_MS),
      PRIORITY_UPDATE_MS,
    );
  }

  private scheduleInactiveStop(state: MusicalState): void {
    if (this.inactiveTimer !== null || !this.playbackActive) {
      return;
    }
    const graceMs = Math.max(
      Number(state.scene?.inactive_grace_ms ?? INACTIVE_GRACE_MS),
      INACTIVE_GRACE_MS,
    );
    this.inactiveTimer = window.setTimeout(() => {
      this.inactiveTimer = null;
      this.targetState = null;
      this.smoothedState = null;
      this.lastStructureKey = "";
      this.stopScheduler();
    }, graceMs);
  }

  private cancelInactiveStop(): void {
    if (this.inactiveTimer === null) {
      return;
    }
    window.clearTimeout(this.inactiveTimer);
    this.inactiveTimer = null;
  }

  private stopScheduler(force = false): void {
    if ((!this.playbackActive && !force) || this.repl === null) {
      return;
    }
    this.repl.stop();
    this.playbackActive = false;
    this.smoothedState = null;
    this.lastCyclesPerMinute = null;
  }
}

function interpolate(current: number, target: number, alpha: number): number {
  return current + (target - current) * alpha;
}
