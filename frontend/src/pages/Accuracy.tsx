import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { fmtMW, fmtPct } from "../api/format";
import { Async, Card, Kpi } from "../components/ui";
import { useApi } from "../hooks/useApi";

export default function Accuracy({ cutoffDefault }: { cutoffDefault: string }) {
  const [from, setFrom] = useState("2026-01-01");
  const [to, setTo] = useState("2026-01-31");
  const [cutoff, setCutoff] = useState(cutoffDefault);
  const [hmax, setHmax] = useState("");
  const p = { from, to, cutoff, horizon_max: hmax || undefined };
  const sum = useApi("/accuracy/summary", p), hour = useApi("/accuracy/by-hour", p), hor = useApi("/accuracy/by-horizon", p),
    day = useApi("/accuracy/by-day", p), reg = useApi("/accuracy/by-regime", p), dist = useApi("/accuracy/error-distribution", p),
    sc = useApi("/accuracy/scatter", p), worst = useApi("/accuracy/worst-errors", p);
  const bar = (data: any[], key: string, label: string, x = "key") => (
    <ResponsiveContainer width="100%" height={260}><BarChart data={data}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey={x} /><YAxis width={70} />
      <Tooltip formatter={(v: number) => fmtMW(v)} /><Legend /><Bar dataKey={key} name={label} fill="#0b6bcb" /></BarChart></ResponsiveContainer>);

  return (<>
    <div className="row">
      <label>Decision from<input type="date" min="2026-01-01" max="2026-01-31" value={from} onChange={(e) => setFrom(e.target.value)} /></label>
      <label>to<input type="date" min="2026-01-01" max="2026-01-31" value={to} onChange={(e) => setTo(e.target.value)} /></label>
      <label>Cut-off (UK)<input type="time" value={cutoff} onChange={(e) => setCutoff(e.target.value)} /></label>
      <label>Max horizon (h)<input type="number" min="1" placeholder="any" value={hmax} onChange={(e) => setHmax(e.target.value)} /></label>
    </div>
    <Async s={sum}>{(s: any) => (<>
      <div className="insight">{s.insight}</div>
      <div className="kpis">
        <Kpi label="MAE" value={fmtMW(s.mae_mw)} tip="Mean absolute error: average size of miss" />
        <Kpi label="RMSE" value={fmtMW(s.rmse_mw)} tip="Root mean squared error: penalises large misses" />
        <Kpi label="Bias (ME)" value={fmtMW(s.bias_mw)} tip="Mean of forecast − actual. Positive = over-forecast = under-buy risk" />
        <Kpi label="90% error band" value={`${fmtMW(s.p5)} to ${fmtMW(s.p95)}`} tip="5th–95th percentile of forecast − actual" />
        <Kpi label="Buffer (90%, one-sided)" value={fmtMW(s.buffer90_mw)} tip="P90 of over-forecast: volume to hold back for under-buy risk" />
        <Kpi label="Normalised MAE" value={fmtPct(s.nmae_pct)} tip="MAE as % of mean actual wind" />
        <Kpi label="sMAPE" value={fmtPct(s.smape_pct)} tip="Symmetric MAPE, guarded near zero" />
        <Kpi label="R²" value={s.r2 == null ? "–" : s.r2.toFixed(3)} tip="Share of actual variance explained by forecast" />
        <Kpi label="Skill vs persistence" value={s.skill_vs_persistence == null ? "–" : `${(100 * s.skill_vs_persistence).toFixed(0)}%`} tip="1 − MAE_forecast / MAE_persistence (actual 24h earlier). >0 beats baseline" />
      </div>
    </>)}</Async>
    <div className="grid2">
      <Card title="Error distribution (forecast − actual, MW)"><Async s={dist}>{(d: any) => bar(d.map((b: any) => ({ ...b, x: Math.round((b.binStart + b.binEnd) / 2) })), "count", "Half-hours", "x")}</Async></Card>
      <Card title="MAE by local hour"><Async s={hour}>{(d: any) => bar(d, "mae_mw", "MAE")}</Async></Card>
      <Card title="MAE by forecast horizon"><Async s={hor}>{(d: any) => bar(d, "mae_mw", "MAE")}</Async></Card>
      <Card title="MAE by wind regime"><Async s={reg}>{(d: any) => bar(d, "mae_mw", "MAE")}</Async></Card>
      <Card title="Daily MAE and bias"><Async s={day}>{(d: any) => (
        <ResponsiveContainer width="100%" height={260}><LineChart data={d}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="key" tickFormatter={(v) => v.slice(5)} /><YAxis width={70} />
          <Tooltip formatter={(v: number) => fmtMW(v)} /><Legend /><Line dataKey="mae_mw" name="MAE" stroke="#0b6bcb" /><Line dataKey="bias_mw" name="Bias" stroke="#e07b00" /></LineChart></ResponsiveContainer>)}</Async></Card>
      <Card title="Forecast vs actual"><Async s={sc}>{(d: any) => (
        <ResponsiveContainer width="100%" height={260}><ScatterChart><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" dataKey="actual" name="Actual" unit=" MW" /><YAxis type="number" dataKey="forecast" name="Forecast" unit=" MW" width={80} />
          <Tooltip /><Scatter data={d} fill="#0b6bcb" /></ScatterChart></ResponsiveContainer>)}</Async></Card>
    </div>
    <Card title="Worst misses"><Async s={worst}>{(d: any) => (<div className="scroll"><table><thead><tr><th>Local time</th><th>Forecast</th><th>Actual</th><th>Error</th><th>Horizon</th></tr></thead>
      <tbody>{d.map((r: any) => (<tr key={r.localTime}><td>{r.localTime}</td><td>{fmtMW(r.forecastMW)}</td><td>{fmtMW(r.actualMW)}</td><td>{fmtMW(r.errorMW)}</td><td>{r.horizonHours.toFixed(1)} h</td></tr>))}</tbody></table></div>)}</Async></Card>
  </>);
}
