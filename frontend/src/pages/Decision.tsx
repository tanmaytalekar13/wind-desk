import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtMW, fmtTime } from "../api/format";
import { Async, Card, Kpi } from "../components/ui";
import { useApi } from "../hooks/useApi";

export default function Decision({ cutoffDefault }: { cutoffDefault: string }) {
  const [date, setDate] = useState("2026-01-15");
  const [cutoff, setCutoff] = useState(cutoffDefault);
  const s = useApi("/decision-forecast", { decision_date: date, cutoff });

  const csv = (rows: any[]) => {
    const h = "localTime,forecastMW,publishTime,horizonHours,actualMW\n";
    const b = rows.map((r) => [r.localTime, r.forecastMW ?? "", r.publishTime ?? "", r.horizonHours?.toFixed(2) ?? "", r.actualMW ?? ""].join(",")).join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([h + b], { type: "text/csv" }));
    a.download = `decision_${date}.csv`;
    a.click();
  };

  return (<>
    <div className="row">
      <label>Decision day (D-1)<input type="date" min="2026-01-01" max="2026-01-31" value={date} onChange={(e) => setDate(e.target.value)} /></label>
      <label>Cut-off (UK time)<input type="time" value={cutoff} onChange={(e) => setCutoff(e.target.value)} /></label>
    </div>
    <Async s={s}>{(d: any) => (<>
      <p>Delivery day <b>{d.delivery_date}</b>. Using the latest forecast published at or before <b>{fmtTime(d.cutoff_utc)}</b> (UK time).</p>
      <div className="kpis">
        <Kpi label="Peak wind" value={fmtMW(d.summary.peak_mw)} tip="Highest forecast half-hour (MW)" />
        <Kpi label="Mean wind" value={fmtMW(d.summary.mean_mw)} tip="Average forecast over delivery day" />
        <Kpi label="Min wind" value={fmtMW(d.summary.min_mw)} tip="Lowest forecast half-hour" />
        <Kpi label={`Low-wind periods`} value={`${d.summary.low_wind_periods}`} tip={`Half-hours forecast below ${d.summary.low_wind_threshold_mw} MW`} />
        <Kpi label="Forecast age" value={d.summary.horizon_min_h == null ? "–" : `${d.summary.horizon_min_h.toFixed(0)}–${d.summary.horizon_max_h.toFixed(0)} h`} tip="Hours between publication and target half-hour" />
        <Kpi label="Missing periods" value={`${d.summary.missing_periods}/${d.summary.periods}`} tip="Half-hours with no forecast available before cut-off (never filled)" />
      </div>
      <Card title="Latest available forecast vs actual">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={d.rows.map((r: any) => ({ ...r, t: r.localTime.slice(11) }))}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="t" interval={3} /><YAxis tickFormatter={(v) => `${v}`} unit=" MW" width={80} />
            <Tooltip formatter={(v: number) => fmtMW(v)} /><Legend />
            <Line dataKey="forecastMW" name="Forecast" stroke="#0b6bcb" dot={false} strokeWidth={2} />
            <Line dataKey="actualMW" name="Actual" stroke="#e07b00" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>
      <Card title="Half-hourly detail">
        <button className="primary" onClick={() => csv(d.rows)}>Download CSV</button>
        <div className="scroll"><table><thead><tr><th>Local time</th><th>Forecast</th><th>Published (UK)</th><th>Horizon</th><th>Actual</th></tr></thead>
          <tbody>{d.rows.map((r: any) => (<tr key={r.startTime}><td>{r.localTime}</td><td>{r.missing ? "missing" : fmtMW(r.forecastMW)}</td>
            <td>{fmtTime(r.publishTime)}</td><td>{r.horizonHours == null ? "–" : `${r.horizonHours.toFixed(1)} h`}</td><td>{fmtMW(r.actualMW)}</td></tr>))}</tbody></table></div>
      </Card>
    </>)}</Async>
  </>);
}
