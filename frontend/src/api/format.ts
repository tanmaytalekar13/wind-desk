export const fmtMW = (n: number | null | undefined): string =>
  n == null || Number.isNaN(n) ? "–" : `${Math.round(n).toLocaleString("en-GB")} MW`;
export const fmtPct = (n: number | null | undefined): string => (n == null ? "–" : `${n.toFixed(1)}%`);
export const fmtTime = (iso: string | null): string =>
  iso ? new Date(iso).toLocaleString("en-GB", { timeZone: "Europe/London", dateStyle: "short", timeStyle: "short" }) : "–";
