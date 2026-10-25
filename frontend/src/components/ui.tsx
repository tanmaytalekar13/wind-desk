import { ReactNode } from "react";
import { ApiState } from "../hooks/useApi";

export const Kpi = ({ label, value, tip }: { label: string; value: string; tip: string }) => (
  <div className="kpi"><span title={tip}>{label}</span><b>{value}</b></div>
);

export function Async<T>({ s, children }: { s: ApiState<T>; children: (d: T) => ReactNode }) {
  if (s.loading && !s.data) return <p className="muted">Loading…</p>;
  if (s.error) return <p className="err">{s.error}</p>;
  if (!s.data || (Array.isArray(s.data) && s.data.length === 0)) return <p className="muted">No data for this selection.</p>;
  return <>{children(s.data)}</>;
}

export const Card = ({ title, children }: { title: string; children: ReactNode }) => (
  <div className="card"><h3>{title}</h3>{children}</div>
);
