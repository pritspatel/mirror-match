import type { ComparePayload, CompareResponse } from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "";

export async function compareJson(
  payload: ComparePayload,
): Promise<CompareResponse> {
  const res = await fetch(`${BASE}/api/v1/compare`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`compare failed: ${res.status} ${text}`);
  }
  return res.json();
}

async function downloadBlob(
  path: string,
  payload: ComparePayload,
  filenameExt: string,
): Promise<void> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `jsondiff-${new Date().toISOString().replace(/[:.]/g, "-")}.${filenameExt}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const downloadCsv = (p: ComparePayload) => downloadBlob("/api/v1/compare.csv", p, "csv");
export const downloadHtml = (p: ComparePayload) => downloadBlob("/api/v1/compare.html", p, "html");
