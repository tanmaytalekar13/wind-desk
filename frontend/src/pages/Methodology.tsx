import { Async, Card } from "../components/ui";
import { useApi } from "../hooks/useApi";

export default function Methodology() {
  const m = useApi("/meta", {});
  return (<Async s={m}>{(d: any) => (<>
    <Card title="Sources">Elexon Insights (BMRS): <code>WINDFOR</code> (national wind forecasts with publish times) and <code>FUELHH</code> (half-hourly outturn, WIND). {d.attribution}.</Card>
    <Card title="Decision rule">For delivery day D, the forecast used for each half-hour is the most recent one published at or before the cut-off on D-1 (default {d.default_cutoff} UK time, configurable). Forecasts published after the cut-off are never used. Scope: decisions {d.scope.decision_from} to {d.scope.decision_to} (delivery {d.scope.delivery_from} to {d.scope.delivery_to}).</Card>
    <Card title="Metrics">{d.sign_convention}. MAE, RMSE, bias, normalised MAE (% of mean actual), sMAPE (guarded near zero), R², P5–P95 error band. Buffer = P90 of the error (over-forecast side). Skill = 1 − MAE/MAE of persistence (actual 24 h earlier). Wind regimes: low &lt; {d.regimes_mw.low_below} MW, high &gt; {d.regimes_mw.high_above} MW.</Card>
    <Card title="Limitations">Wind only: demand, solar and prices are out of scope. One month of data; error statistics are not a guarantee. Persistence baseline uses actual 24 h earlier in UTC. Half-hours without a forecast are flagged, not filled. {d.ingest?.ingested_at && `Snapshot ingested ${d.ingest.ingested_at}.`}</Card>
  </>)}</Async>);
}
