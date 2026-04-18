import { useMemo, useState } from "react";
import { EditorPane } from "./components/EditorPane";
import { DiffView } from "./components/DiffView";
import { compareJson, downloadCsv } from "./api/client";
import type { ComparePayload, CompareResponse } from "./types";

const SAMPLE_A = `{
  "user": { "id": 42, "name": "Alice" },
  "orders": [ { "id": 1, "price": 10 } ],
  "legacy_flag": true
}`;

const SAMPLE_B = `{
  "user": { "id": 42, "name": "Alicia", "tier": "gold" },
  "orders": [ { "id": 1, "price": 12 } ]
}`;

function parseJson(
  text: string,
): { ok: true; value: unknown } | { ok: false; error: string } {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch (e) {
    return { ok: false, error: (e as Error).message };
  }
}

export default function App() {
  const [textA, setTextA] = useState(SAMPLE_A);
  const [textB, setTextB] = useState(SAMPLE_B);
  const [idA, setIdA] = useState("doc-a");
  const [idB, setIdB] = useState("doc-b");
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const payload = useMemo<ComparePayload | null>(() => {
    const a = parseJson(textA);
    const b = parseJson(textB);
    if (!a.ok || !b.ok) return null;
    return {
      source_a: { type: "raw", data: a.value, identifier: idA || "doc-a" },
      source_b: { type: "raw", data: b.value, identifier: idB || "doc-b" },
    };
  }, [textA, textB, idA, idB]);

  async function runCompare() {
    setError(null);
    const a = parseJson(textA);
    const b = parseJson(textB);
    if (!a.ok) return setError(`Source A invalid JSON: ${a.error}`);
    if (!b.ok) return setError(`Source B invalid JSON: ${b.error}`);
    setBusy(true);
    try {
      const res = await compareJson(payload!);
      setResult(res);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function exportCsv() {
    if (!payload) return setError("Fix JSON parse errors before exporting.");
    setBusy(true);
    try {
      await downloadCsv(payload);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>JSONDiff</h1>
        <span className="meta">v0.1 · raw JSON mode</span>
      </header>
      <main>
        <div className="editors">
          <EditorPane
            label="Source A"
            identifier={idA}
            onIdentifierChange={setIdA}
            value={textA}
            onChange={setTextA}
          />
          <EditorPane
            label="Source B"
            identifier={idB}
            onIdentifierChange={setIdB}
            value={textB}
            onChange={setTextB}
          />
        </div>
        <div className="toolbar">
          <button onClick={runCompare} disabled={busy || !payload}>
            Compare
          </button>
          <button className="secondary" onClick={exportCsv} disabled={busy || !payload}>
            Export CSV
          </button>
          {!payload && <span className="error">Invalid JSON in one or both panes</span>}
        </div>
        {error && <div className="error">{error}</div>}
        <DiffView result={result} />
      </main>
    </div>
  );
}
