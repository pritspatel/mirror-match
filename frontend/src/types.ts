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

export type AuthKind = "none" | "bearer" | "basic" | "api_key";

export interface RawSourceConfig {
  type: "raw";
  data: unknown;
  identifier?: string;
}

export interface HttpSourceConfig {
  type: "http";
  url: string;
  method: "GET" | "POST";
  headers: Record<string, string>;
  body?: unknown;
  auth: {
    kind: AuthKind;
    token?: string;
    username?: string;
    password?: string;
    header_name?: string;
  };
  json_pointer?: string;
  identifier?: string;
}

export type EsAuthKind = "none" | "api_key" | "basic";

export interface EsSourceConfig {
  type: "elasticsearch";
  hosts: string[];
  index: string;
  mode: "by_id" | "query";
  doc_id?: string;
  query?: Record<string, unknown>;
  query_return: "first_source" | "hits";
  auth: {
    kind: EsAuthKind;
    api_key?: string;
    username?: string;
    password?: string;
  };
  verify_certs: boolean;
  identifier?: string;
}

export type SourceConfig = RawSourceConfig | HttpSourceConfig | EsSourceConfig;

export type SourceKind = SourceConfig["type"];

export interface ComparePayload {
  source_a: SourceConfig;
  source_b: SourceConfig;
  options?: {
    ignore_paths?: string[];
    array_as_set?: boolean;
    array_keys?: Record<string, string>;
    numeric_tolerance?: number;
    case_insensitive?: boolean;
  };
}

export interface CompareOptions {
  ignore_paths: string[];
  array_as_set: boolean;
  array_keys: Record<string, string>;
  numeric_tolerance: number;
  case_insensitive: boolean;
}
