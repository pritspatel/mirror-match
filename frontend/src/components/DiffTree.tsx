import { useMemo, useState } from "react";
import type { CompareResponse, FieldChange } from "../types";

type Node = {
  name: string;
  path: string;
  children: Record<string, Node>;
  change?: FieldChange;
};

function buildTree(changes: FieldChange[]): Node {
  const root: Node = { name: "", path: "", children: {} };
  for (const c of changes) {
    const tokens = c.path.split("/").filter(Boolean);
    let node = root;
    let acc = "";
    for (let i = 0; i < tokens.length; i++) {
      const t = tokens[i];
      acc = `${acc}/${t}`;
      if (!node.children[t]) {
        node.children[t] = { name: t, path: acc, children: {} };
      }
      node = node.children[t];
      if (i === tokens.length - 1) node.change = c;
    }
    if (tokens.length === 0) root.change = c;
  }
  return root;
}

function fmt(value: unknown): string {
  if (value === undefined) return "";
  if (value === null) return "null";
  if (typeof value === "string") return JSON.stringify(value);
  return JSON.stringify(value, null, 0);
}

function TreeNode({
  node,
  expanded,
  toggle,
  depth = 0,
}: {
  node: Node;
  expanded: Set<string>;
  toggle: (p: string) => void;
  depth?: number;
}) {
  const keys = Object.keys(node.children).sort();
  const hasChildren = keys.length > 0;
  const isOpen = expanded.has(node.path);
  const badge = node.change?.change_type;
  const rowClass = `tree-row${badge ? ` row-${badge}` : ""}`;

  return (
    <>
      <div
        className={rowClass}
        style={{ paddingLeft: depth * 14 + 8 }}
        onClick={hasChildren ? () => toggle(node.path) : undefined}
      >
        <span className="toggle">
          {hasChildren ? (isOpen ? "▼" : "▶") : "·"}
        </span>
        <span className="node-name">{node.name || "/"}</span>
        {node.change && (
          <span className="node-change">
            {badge === "MODIFIED" && (
              <>
                <span className="old">{fmt(node.change.value_a)}</span>
                <span className="arrow">→</span>
                <span className="new">{fmt(node.change.value_b)}</span>
              </>
            )}
            {badge === "ADDED" && <span className="new">+ {fmt(node.change.value_b)}</span>}
            {badge === "REMOVED" && <span className="old">− {fmt(node.change.value_a)}</span>}
          </span>
        )}
      </div>
      {isOpen &&
        keys.map((k) => (
          <TreeNode
            key={node.children[k].path}
            node={node.children[k]}
            expanded={expanded}
            toggle={toggle}
            depth={depth + 1}
          />
        ))}
    </>
  );
}

function collectExpandable(node: Node, acc: Set<string>) {
  if (Object.keys(node.children).length > 0) acc.add(node.path);
  for (const k of Object.keys(node.children)) collectExpandable(node.children[k], acc);
}

export function DiffTree({ result }: { result: CompareResponse | null }) {
  const tree = useMemo(
    () => (result ? buildTree(result.changes) : null),
    [result],
  );
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set([""]));

  if (!result) return <div className="empty">Configure sources, then Compare.</div>;
  if (result.changes.length === 0)
    return <div className="empty">No differences. Documents are identical.</div>;

  function toggle(p: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });
  }

  function expandAll() {
    if (!tree) return;
    const all = new Set<string>([""]);
    collectExpandable(tree, all);
    setExpanded(all);
  }

  function collapseAll() {
    setExpanded(new Set([""]));
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
        <button className="link" onClick={expandAll}>
          Expand all
        </button>
        <button className="link" onClick={collapseAll}>
          Collapse all
        </button>
      </div>
      <div className="tree">
        {tree && (
          <TreeNode node={tree} expanded={expanded} toggle={toggle} />
        )}
      </div>
    </div>
  );
}
