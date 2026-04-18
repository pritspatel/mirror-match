export type ChangeType = "ADDED" | "REMOVED" | "MODIFIED";

export interface FieldChange {
  path: string;
  change_type: ChangeType;
  value_a: unknown;
  value_b: unknown;
}

export interface DiffSummary {
  added: number;
  removed: number;
  modified: number;
  total: number;
}

export interface CompareResponse {
  job_id: string;
  timestamp: string;
  source_a_id: string;
  source_b_id: string;
  summary: DiffSummary;
  changes: FieldChange[];
}

export interface ComparePayload {
  source_a: { type: "raw"; data: unknown; identifier?: string };
  source_b: { type: "raw"; data: unknown; identifier?: string };
  options?: { ignore_paths?: string[] };
}
