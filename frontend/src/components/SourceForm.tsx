import Editor from "@monaco-editor/react";
import type { SourceConfig, SourceKind } from "../types";

interface Props {
  label: string;
  value: SourceConfig;
  rawText: string;
  onRawTextChange: (v: string) => void;
  onChange: (v: SourceConfig) => void;
}

const KINDS: { value: SourceKind; label: string }[] = [
  { value: "raw", label: "Raw JSON" },
  { value: "http", label: "HTTP" },
  { value: "elasticsearch", label: "Elasticsearch" },
];

function defaultForKind(kind: SourceKind, identifier?: string): SourceConfig {
  if (kind === "raw") return { type: "raw", data: {}, identifier };
  if (kind === "http")
    return {
      type: "http",
      url: "",
      method: "GET",
      headers: {},
      auth: { kind: "none" },
      identifier,
    };
  return {
    type: "elasticsearch",
    hosts: ["http://localhost:9200"],
    index: "",
    mode: "by_id",
    query_return: "first_source",
    auth: { kind: "none" },
    verify_certs: true,
    identifier,
  };
}

export function SourceForm({
  label,
  value,
  rawText,
  onRawTextChange,
  onChange,
}: Props) {
  const identifier = value.identifier ?? "";

  function setKind(kind: SourceKind) {
    onChange(defaultForKind(kind, value.identifier));
  }

  function patch<T extends SourceConfig>(next: Partial<T>) {
    onChange({ ...(value as T), ...next });
  }

  return (
    <div className="source-form">
      <div className="form-header">
        <strong>{label}</strong>
        <select
          value={value.type}
          onChange={(e) => setKind(e.target.value as SourceKind)}
        >
          {KINDS.map((k) => (
            <option key={k.value} value={k.value}>
              {k.label}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="identifier"
          value={identifier}
          onChange={(e) => patch({ identifier: e.target.value })}
        />
      </div>

      {value.type === "raw" && (
        <div className="editor-host">
          <Editor
            language="json"
            theme="vs-dark"
            value={rawText}
            onChange={(v) => onRawTextChange(v ?? "")}
            options={{
              minimap: { enabled: false },
              fontSize: 13,
              wordWrap: "on",
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        </div>
      )}

      {value.type === "http" && (
        <div className="form-body">
          <label>
            URL
            <input
              type="text"
              value={value.url}
              onChange={(e) => patch({ url: e.target.value })}
              placeholder="https://api.example.com/resource"
            />
          </label>
          <div className="row">
            <label>
              Method
              <select
                value={value.method}
                onChange={(e) => patch({ method: e.target.value as "GET" | "POST" })}
              >
                <option>GET</option>
                <option>POST</option>
              </select>
            </label>
            <label>
              Auth
              <select
                value={value.auth.kind}
                onChange={(e) =>
                  patch({
                    auth: {
                      ...value.auth,
                      kind: e.target.value as typeof value.auth.kind,
                    },
                  })
                }
              >
                <option value="none">None</option>
                <option value="bearer">Bearer</option>
                <option value="basic">Basic</option>
                <option value="api_key">API Key</option>
              </select>
            </label>
          </div>
          {(value.auth.kind === "bearer" || value.auth.kind === "api_key") && (
            <label>
              Token
              <input
                type="password"
                value={value.auth.token ?? ""}
                onChange={(e) =>
                  patch({ auth: { ...value.auth, token: e.target.value } })
                }
              />
            </label>
          )}
          {value.auth.kind === "api_key" && (
            <label>
              Header name
              <input
                type="text"
                value={value.auth.header_name ?? "X-API-Key"}
                onChange={(e) =>
                  patch({
                    auth: { ...value.auth, header_name: e.target.value },
                  })
                }
              />
            </label>
          )}
          {value.auth.kind === "basic" && (
            <div className="row">
              <label>
                Username
                <input
                  type="text"
                  value={value.auth.username ?? ""}
                  onChange={(e) =>
                    patch({ auth: { ...value.auth, username: e.target.value } })
                  }
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  value={value.auth.password ?? ""}
                  onChange={(e) =>
                    patch({ auth: { ...value.auth, password: e.target.value } })
                  }
                />
              </label>
            </div>
          )}
          <label>
            JSON Pointer (optional)
            <input
              type="text"
              value={value.json_pointer ?? ""}
              placeholder="/data/item"
              onChange={(e) => patch({ json_pointer: e.target.value || undefined })}
            />
          </label>
          {value.method === "POST" && (
            <label>
              Request body (JSON)
              <textarea
                rows={4}
                value={
                  value.body === undefined ? "" : JSON.stringify(value.body, null, 2)
                }
                onChange={(e) => {
                  try {
                    patch({ body: e.target.value ? JSON.parse(e.target.value) : undefined });
                  } catch {
                    /* ignore parse errors while typing */
                  }
                }}
              />
            </label>
          )}
        </div>
      )}

      {value.type === "elasticsearch" && (
        <div className="form-body">
          <label>
            Hosts (comma-separated)
            <input
              type="text"
              value={value.hosts.join(",")}
              onChange={(e) =>
                patch({
                  hosts: e.target.value
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                })
              }
            />
          </label>
          <div className="row">
            <label>
              Index
              <input
                type="text"
                value={value.index}
                onChange={(e) => patch({ index: e.target.value })}
              />
            </label>
            <label>
              Mode
              <select
                value={value.mode}
                onChange={(e) => patch({ mode: e.target.value as "by_id" | "query" })}
              >
                <option value="by_id">by id</option>
                <option value="query">query (first hit)</option>
              </select>
            </label>
          </div>
          {value.mode === "by_id" ? (
            <label>
              Doc ID
              <input
                type="text"
                value={value.doc_id ?? ""}
                onChange={(e) => patch({ doc_id: e.target.value })}
              />
            </label>
          ) : (
            <label>
              DSL query (JSON)
              <textarea
                rows={5}
                value={
                  value.query === undefined
                    ? '{ "query": { "match_all": {} } }'
                    : JSON.stringify(value.query, null, 2)
                }
                onChange={(e) => {
                  try {
                    patch({ query: JSON.parse(e.target.value) });
                  } catch {
                    /* ignore parse errors while typing */
                  }
                }}
              />
            </label>
          )}
          <div className="row">
            <label>
              Auth
              <select
                value={value.auth.kind}
                onChange={(e) =>
                  patch({
                    auth: {
                      ...value.auth,
                      kind: e.target.value as typeof value.auth.kind,
                    },
                  })
                }
              >
                <option value="none">None</option>
                <option value="api_key">API Key</option>
                <option value="basic">Basic</option>
              </select>
            </label>
            {value.auth.kind === "api_key" && (
              <label>
                API key
                <input
                  type="password"
                  value={value.auth.api_key ?? ""}
                  onChange={(e) =>
                    patch({ auth: { ...value.auth, api_key: e.target.value } })
                  }
                />
              </label>
            )}
            {value.auth.kind === "basic" && (
              <>
                <label>
                  Username
                  <input
                    type="text"
                    value={value.auth.username ?? ""}
                    onChange={(e) =>
                      patch({
                        auth: { ...value.auth, username: e.target.value },
                      })
                    }
                  />
                </label>
                <label>
                  Password
                  <input
                    type="password"
                    value={value.auth.password ?? ""}
                    onChange={(e) =>
                      patch({
                        auth: { ...value.auth, password: e.target.value },
                      })
                    }
                  />
                </label>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
