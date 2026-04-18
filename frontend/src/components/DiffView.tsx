import type { CompareResponse, FieldChange } from "../types";

const BADGE: Record<FieldChange["change_type"], string> = {
  ADDED: "+",
  REMOVED: "−",
  MODIFIED: "~",
};

function fmt(value: unknown): string {
  if (value === undefined || value === null) return "null";
  if (typeof value === "string") return JSON.stringify(value);
  return JSON.stringify(value, null, 0);
}

export function DiffView({ result }: { result: CompareResponse | null }) {
  if (!result) {
    return <div className="empty">Paste JSON into both panes, then Compare.</div>;
  }
  if (result.changes.length === 0) {
    return <div className="empty">No differences. Documents are identical.</div>;
  }
  return (
    <div className="results">
      <div className="summary">
        <span>
          Compared {result.timestamp} · A: <b>{result.source_a_id}</b> · B:{" "}
          <b>{result.source_b_id}</b>
        </span>
        <span className="chip-added">+{result.summary.added}</span>
        <span className="chip-removed">−{result.summary.removed}</span>
        <span className="chip-modified">~{result.summary.modified}</span>
      </div>
      {result.changes.map((c) => (
        <div key={c.path + c.change_type} className={`change-row ${c.change_type}`}>
          <span className="badge">{BADGE[c.change_type]}</span>
          <span className="path">{c.path || "/"}</span>
          <span className="values">
            {c.change_type === "MODIFIED" ? (
              <>
                <span className="old">{fmt(c.value_a)}</span>
                <span className="arrow">→</span>
                <span className="new">{fmt(c.value_b)}</span>
              </>
            ) : c.change_type === "ADDED" ? (
              <span className="new">{fmt(c.value_b)}</span>
            ) : (
              <span className="old">{fmt(c.value_a)}</span>
            )}
          </span>
        </div>
      ))}
    </div>
  );
}
