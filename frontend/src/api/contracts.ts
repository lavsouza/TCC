export type EventType =
  | "session.status.v1"
  | "runtime.status.v1"
  | "music.state.v1"
  | "preview.frame.v1"
  | "profile.selected.v1"
  | "error.v1";

export interface EventEnvelope<T = Record<string, unknown>> {
  schema_version: "1.0";
  type: EventType;
  timestamp: number;
  session_id: string | null;
  data: T;
}

export interface Session {
  id: string;
  selected_profile: string;
  profile_source: string;
  created_at: number;
}

export interface LayerRecipe {
  id: string;
  kind: "note" | "sample";
  pattern: string;
  sound: string;
  use_motion_synth: boolean;
  note_offset: number;
  intervals: string;
  gain: number;
  follow_filter: boolean;
  lpf_ratio: number;
  hpf: number;
  attack: number;
  release: number;
  room: number;
  delay: number;
  delay_time: number;
  shape: number;
  distort: number;
  crush: number;
  pan: string;
  fast: number;
  slow: number;
  euclid: [number, number, number] | null;
  palindrome: boolean;
}

export interface GestureRecipe {
  pinch_gain: number;
  pinch_lpf_offset: number;
  pinch_fast: number;
  pinch_shape: number;
  release_gain: number;
  release_room: number;
  release_delay: number;
  hold_layer: LayerRecipe;
  sweep_left: string;
  sweep_right: string;
  sweep_amount: number;
}

export interface Scene {
  id: string;
  name: string;
  description: string;
  beats_per_cycle: number;
  master_gain: number;
  continuous_update_ms: number;
  inactive_grace_ms: number;
  synth_change_priority: boolean;
  mode_action: string;
  mode_amount: number;
  mode_layer_gain: number;
  layers: LayerRecipe[];
  gesture: GestureRecipe;
}

export interface EmotionProfile {
  id: string;
  emotion: string;
  label: string;
  name: string;
  description: string;
  bpm: number;
  density: number;
  intensity: number;
  gain_range: [number, number];
  lpf_range: [number, number];
  synth_family: string[];
  scale_notes: string[];
  rhythm_patterns: string[];
  variation: number;
  transition_seconds: number;
  scene: {
    id: string;
    name: string;
    description: string;
    beats_per_cycle: number;
    layers: string[];
  };
}

export interface Catalog {
  schema_version: "1.0";
  default_profile_id: string;
  profiles: EmotionProfile[];
}

export interface MusicalState {
  active: boolean;
  note_label: string;
  strudel_note: string;
  frequency: number;
  gain: number;
  brightness: number;
  lpf: number;
  synth: string;
  hands_detected: number;
  primary_handedness: string;
  secondary_handedness: string;
  brightness_source: string;
  gesture_phase: string;
  gesture_event: string;
  gesture_label: string;
  sweep_direction: string;
  pattern_mode: string;
  emotion: string;
  emotion_label: string;
  emotion_source: string;
  emotion_confidence: number;
  selected_profile: string;
  profile_name: string;
  profile_description: string;
  profile_bpm: number;
  profile_density: number;
  profile_intensity: number;
  profile_variation: number;
  profile_transition_seconds: number;
  profile_rhythm: string;
  scene: Scene;
  scene_name: string;
  scene_layers: string[];
  scene_beats_per_cycle: number;
  selected_preset?: string;
  preset_bpm?: number;
  preset_density?: number;
  preset_rhythm?: string;
}

export interface PreviewFrame {
  image: string;
  width: number;
  height: number;
  timestamp: number;
}

export interface ErrorEvent {
  code: string;
  detail: string;
}
