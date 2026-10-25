const BASE: string = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

export async function get<T = any>(path: string, params: Record<string, string | number | undefined> = {}): Promise<T> {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && q.set(k, String(v)));
  const r = await fetch(`${BASE}/api${path}?${q}`);
  if (!r.ok) {
    const j = await r.json().catch(() => ({}));
    throw new Error(typeof j.detail === "string" ? j.detail : r.statusText);
  }
  return r.json();
}
