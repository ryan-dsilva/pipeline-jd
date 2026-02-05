// ── Pipeline stages ─────────────────────────────────────────────

export const PIPELINE_STAGES = [
  "queue",
  "analyzing",
  "analyzed",
  "cover_letter_gen",
  "ready",
  "applied",
  "ignored",
] as const;

export type PipelineStage = (typeof PIPELINE_STAGES)[number];

export const VERDICTS = [
  "STRONG PURSUE",
  "PURSUE",
  "PASS",
  "HARD PASS",
] as const;

export type Verdict = (typeof VERDICTS)[number];

// ── Jobs ────────────────────────────────────────────────────────

export interface JobCreate {
  jd_url: string;
  jd_text?: string;
  jd_fetch_status?: string;
  jd_fetch_confidence?: number;
}

export interface Job {
  id: string;
  company: string;
  role: string;
  jd_url: string | null;
  jd_text: string | null;
  jd_cleaned: string | null;
  date_added: string;
  date_posted: string | null;
  pipeline_stage: PipelineStage;
  score: number | null;
  hours: number | null;
  verdict: Verdict | null;
  extraction_status: string;
  jd_fetch_status: string;
  jd_fetch_confidence: number | null;
  created: string;
  updated: string;
}

export interface JobDetail extends Job {
  sections: Section[];
}

// ── Sections ────────────────────────────────────────────────────

export type SectionStatus = "pending" | "running" | "complete" | "failed";

export interface Section {
  id: string;
  job: string;
  section_key: string;
  phase: "analysis" | "cover_letter";
  status: SectionStatus;
  content_md: string | null;
  model: string | null;
  tokens_used: number | null;
  generation_time_ms: number | null;
  error_message: string | null;
  is_locked: boolean;
  created: string;
  updated: string;
}

export interface SectionDefinition {
  key: string;
  label: string;
  order: number;
  depends_on: string[];
  phase: "analysis" | "cover_letter";
}

// ── Pipeline ────────────────────────────────────────────────────

export interface PipelineEvent {
  section_key: string;
  status: SectionStatus;
  content_md?: string;
  error_message?: string;
}

// ── Chat ────────────────────────────────────────────────────────

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
