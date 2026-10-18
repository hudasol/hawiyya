// Data access for live mode (local API under /v1) and static mode (precomputed snapshot).
import type { PairScore } from "./contract/types";

export const MODE: "live" | "static" =
  import.meta.env.VITE_HAWIYYA_MODE === "static" ? "static" : "live";

const SNAPSHOT = `${import.meta.env.BASE_URL}snapshot/`;

export interface Envelope {
  synthetic_note: string;
  advisory_note: string;
  mode: string;
}

export interface Summary extends Envelope {
  records: number;
  facilities: { facility_id: string; style: string; description: string }[];
  placeholder_identifier_share: number;
  suspected_default_dob_share: number;
  data_source: string;
  model_version: string;
  synthetic_ground_truth: { label: string; persons: number; duplicate_record_share: number };
}

export interface RegistrationInput {
  name_ar?: string | null;
  name_latin?: string | null;
  sex?: "M" | "F" | null;
  dob?: string | null;
  id_value?: string | null;
  phone?: string | null;
  top?: number;
}

export interface Candidate {
  record: Record<string, string | null>;
  score: PairScore;
  decision?: {
    decision: "LINK" | "REVIEW" | "KEEP_APART";
    reason_codes: string[];
    guards_fired: string[];
    explanation?: { en: string[]; ar: string[] };
  } | null;
}

export interface CheckResponse extends Envelope {
  ok: boolean;
  n_scored: number;
  candidates: Candidate[];
  note: string;
  next_best_question?:
    | {
        key: string;
        field: string;
        expected_cost_reduction: number;
        label_en: string;
        label_ar: string;
      }[]
    | null;
}

export interface CheckExample {
  key: string;
  label: string;
  input: RegistrationInput;
  response: CheckResponse;
}

export interface NameAnalysis extends Envelope {
  input_script: string;
  normalised: string;
  tokens: { token: string; skeleton: string; coarse: string }[];
  structure: Record<string, string | string[] | boolean | null>;
  generator_variants: Record<string, string[]>;
  collisions: string[][];
  comparison?: Record<string, { level: string; label_en: string; label_ar: string }>;
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return getJson<T>(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function getSummary(): Promise<Summary> {
  return MODE === "static"
    ? getJson<Summary>(`${SNAPSHOT}registry_summary.json`)
    : getJson<Summary>("/v1/registry/summary");
}

export function postCheck(input: RegistrationInput): Promise<CheckResponse> {
  return post<CheckResponse>("/v1/check", input);
}

export async function getCheckExamples(): Promise<CheckExample[]> {
  const d = await getJson<{ examples: CheckExample[] }>(`${SNAPSHOT}check_examples.json`);
  return d.examples;
}

export function analyseName(name: string, other?: string): Promise<NameAnalysis> {
  return post<NameAnalysis>("/v1/names/analyse", { name, other: other || null });
}

export async function getNameExamples(): Promise<{ name: string; response: NameAnalysis }[]> {
  const d = await getJson<{ examples: { name: string; response: NameAnalysis }[] }>(
    `${SNAPSHOT}names_examples.json`,
  );
  return d.examples;
}
