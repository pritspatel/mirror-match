import { useEffect, useState } from "react";
import { SourceForm } from "./components/SourceForm";
import { DiffView } from "./components/DiffView";
import { DiffTree } from "./components/DiffTree";
import {
  compareJson,
  downloadCsv,
  downloadHtml,
  fetchJob,
  jobCsvUrl,
  jobHtmlUrl,
} from "./api/client";
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

function readJobFromHash(): string | null {
  const m = window.location.hash.match(/^#\/jobs\/([^/]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

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
  const [arrayKeysText, setArrayKeysText] = useState("");
  const [numericTolerance, setNumericTolerance] = useState("0");
  const [caseInsensitive, setCaseInsensitive] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("flat");
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const jobId = readJobFromHash();
    if (!jobId) return;
    setBusy(true);
    fetchJob(jobId)
      .then(setResult)
      .catch((e) => setError((e as Error).message))
      .finally(() => setBusy(false));
  }, []);

  function parseArrayKeys(text: string): Record<string, string> {
    const out: Record<string, string> = {};
    text
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .forEach((pair) => {
        const [pointer, field] = pair.split("=");
        if (pointer && field) out[pointer] = field;
      });
    return out;
  }

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
    const tol = Number.parseFloat(numericTolerance);
    return {
      source_a: a,
      source_b: b,
      options: {
        array_as_set: arrayAsSet,
        ignore_paths: ignore,
        array_keys: parseArrayKeys(arrayKeysText),
        numeric_tolerance: Number.isFinite(tol) ? tol : 0,
        case_insensitive: caseInsensitive,
      },
    };
  }

  async function runCompare() {
    setError(null);
    const payload = buildPayload();
    if (typeof payload === "string") return setError(payload);
    setBusy(true);
    try {
      const res = await compareJson(payload);
      setResult(res);
      window.history.replaceState(null, "", `#/jobs/${res.job_id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function runExport(kind: "csv" | "html") {
    setError(null);
    if (result?.job_id) {
      const url = kind === "csv" ? jobCsvUrl(result.job_id) : jobHtmlUrl(result.job_id);
      window.open(url, "_blank");
      return;
    }
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

  async function copyShareLink() {
    if (!result?.job_id) return;
    const url = `${window.location.origin}${window.location.pathname}#/jobs/${result.job_id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError("clipboard unavailable");
    }
  }

  return (
    <div className="app">
      <header>
        <h1>MirrorMatch</h1>
        <span className="meta">v1.0 · raw · HTTP · Elasticsearch</span>
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
          <button
            className="secondary"
            onClick={copyShareLink}
            disabled={!result?.job_id || busy}
            title={result?.job_id ? `Share job ${result.job_id}` : "Run a compare first"}
          >
            {copied ? "Copied!" : "Share link"}
          </button>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={arrayAsSet}
              onChange={(e) => setArrayAsSet(e.target.checked)}
            />
            Arrays as sets
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={caseInsensitive}
              onChange={(e) => setCaseInsensitive(e.target.checked)}
            />
            Case-insensitive
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
          <label className="checkbox">
            Array keys:
            <input
              type="text"
              value={arrayKeysText}
              placeholder="/items=id,/users=uuid"
              onChange={(e) => setArrayKeysText(e.target.value)}
            />
          </label>
          <label className="checkbox">
            Num tol:
            <input
              type="number"
              step="0.0001"
              value={numericTolerance}
              onChange={(e) => setNumericTolerance(e.target.value)}
              style={{ width: "6rem" }}
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
