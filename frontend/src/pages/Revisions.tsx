import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtMW, fmtTime } from "../api/format";
import { Async, Card } from "../components/ui";
import { useApi } from "../hooks/useApi";

export default function Revisions() {
  const [date, setDate] = useState("2026-01-15");
  const s = useApi("/forecast-vintages", { target_date: date });
  return (<>
    <div className="row"><label>Target (delivery) day<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label></div>
    <Async s={s}>{(d: any) => {
      const step = Math.max(1, Math.floor(d.vintages.length / 10));
      const picked = d.vintages.filter((_: any, i: number) => i % step === 0).slice(-12);
      const byT: Record<string, any> = {};
      d.actual.forEach((a: any) => (byT[a.startTime] = { t: new Date(a.startTime).toLocaleTimeString("en-GB", { timeZone: "Europe/London", hour: "2-digit", minute: "2-digit" }), actual: a.actualMW }));
      picked.forEach((v: any, i: number) => v.points.forEach((p: any) => { if (byT[p.startTime]) byT[p.startTime][`v${i}`] = p.forecastMW; }));
      return (<Card title={`Forecast revisions for ${d.target_date} (${d.vintages.length} vintages, ${picked.length} shown)`}>
        <ResponsiveContainer width="100%" height={380}><LineChart data={Object.values(byT)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="t" interval={3} /><YAxis width={80} />
          <Tooltip formatter={(v: number) => fmtMW(v)} /><Legend />
          {picked.map((v: any, i: number) => <Line key={i} dataKey={`v${i}`} name={`pub ${fmtTime(v.publishTime)}`} dot={false} strokeOpacity={0.35 + 0.05 * i} stroke="#0b6bcb" />)}
          <Line dataKey="actual" name="Actual" stroke="#e07b00" strokeWidth={3} dot={false} /></LineChart></ResponsiveContainer></Card>);
    }}</Async>
  </>);
}
