import { useState } from "react";
import { SourceForm } from "./components/SourceForm";
import { DiffView } from "./components/DiffView";
import { DiffTree } from "./components/DiffTree";
import { compareJson, downloadCsv, downloadHtml } from "./api/client";
import type {
  ComparePayload,
  CompareResponse,
  SourceConfig,
} from "./types";

const SAMPLE_A = `{
  "user": { "id": 42, "name": "Alice" },
  "orders": [ { "id": 1, "price": 10 } ],
  "legacy_flag": true
}`;

const SAMPLE_B = `{
  "user": { "id": 42, "name": "Alicia", "tier": "gold" },
  "orders": [ { "id": 1, "price": 12 } ]
}`;

type ViewMode = "flat" | "tree";

export default function App() {
  const [sourceA, setSourceA] = useState<SourceConfig>({
    type: "raw",
    data: {},
    identifier: "doc-a",
  });
  const [sourceB, setSourceB] = useState<SourceConfig>({
    type: "raw",
    data: {},
    identifier: "doc-b",
  });
  const [rawTextA, setRawTextA] = useState(SAMPLE_A);
  const [rawTextB, setRawTextB] = useState(SAMPLE_B);
  const [arrayAsSet, setArrayAsSet] = useState(false);
  const [ignorePaths, setIgnorePaths] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("flat");
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function buildPayload(): ComparePayload | string {
    const resolve = (s: SourceConfig, rawText: string): SourceConfig | string => {
      if (s.type !== "raw") return s;
      try {
        return { ...s, data: JSON.parse(rawText) };
      } catch (e) {
        return `invalid JSON: ${(e as Error).message}`;
      }
    };
    const a = resolve(sourceA, rawTextA);
    if (typeof a === "string") return `Source A: ${a}`;
    const b = resolve(sourceB, rawTextB);
    if (typeof b === "string") return `Source B: ${b}`;
    const ignore = ignorePaths
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    return {
      source_a: a,
      source_b: b,
      options: { array_as_set: arrayAsSet, ignore_paths: ignore },
    };
  }

  async function runCompare() {
    setError(null);
    const payload = buildPayload();
    if (typeof payload === "string") return setError(payload);
    setBusy(true);
    try {
      setResult(await compareJson(payload));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function runExport(kind: "csv" | "html") {
    setError(null);
    const payload = buildPayload();
    if (typeof payload === "string") return setError(payload);
    setBusy(true);
    try {
      if (kind === "csv") await downloadCsv(payload);
      else await downloadHtml(payload);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>MirrorMatch</h1>
        <span className="meta">v0.2 · raw · HTTP · Elasticsearch</span>
      </header>
      <main>
        <div className="editors">
          <SourceForm
            label="Source A"
            value={sourceA}
            rawText={rawTextA}
            onRawTextChange={setRawTextA}
            onChange={setSourceA}
          />
          <SourceForm
            label="Source B"
            value={sourceB}
            rawText={rawTextB}
            onRawTextChange={setRawTextB}
            onChange={setSourceB}
          />
        </div>
        <div className="toolbar">
          <button onClick={runCompare} disabled={busy}>
            Compare
          </button>
          <button className="secondary" onClick={() => runExport("csv")} disabled={busy}>
            Export CSV
          </button>
          <button className="secondary" onClick={() => runExport("html")} disabled={busy}>
            Export HTML
          </button>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={arrayAsSet}
              onChange={(e) => setArrayAsSet(e.target.checked)}
            />
            Treat arrays as sets
          </label>
          <label className="checkbox">
            Ignore paths:
            <input
              type="text"
              value={ignorePaths}
              placeholder="/meta/ts,/cache"
              onChange={(e) => setIgnorePaths(e.target.value)}
            />
          </label>
          <div className="view-toggle">
            <button
              className={viewMode === "flat" ? "pill active" : "pill"}
              onClick={() => setViewMode("flat")}
            >
              Flat
            </button>
            <button
              className={viewMode === "tree" ? "pill active" : "pill"}
              onClick={() => setViewMode("tree")}
            >
              Tree
            </button>
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        {viewMode === "flat" ? <DiffView result={result} /> : <DiffTree result={result} />}
      </main>
    </div>
  );
}
