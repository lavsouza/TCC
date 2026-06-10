declare module "@strudel/web" {
  export interface StrudelRepl {
    setPattern(pattern: unknown, autostart?: boolean): Promise<void>;
    setCps(cyclesPerSecond: number): void;
    stop(): void;
  }

  export interface PatternLike {
    [method: string]: (...args: unknown[]) => PatternLike;
  }

  export function initStrudel(options?: {
    prebake?: () => unknown;
  }): Promise<StrudelRepl> | StrudelRepl;

  export function samples(source: string): unknown;
  export function note(pattern: string): PatternLike;
  export function s(pattern: string): PatternLike;
  export function stack(...patterns: PatternLike[]): PatternLike;
}
