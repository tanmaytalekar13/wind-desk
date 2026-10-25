import { useState } from "react";
import Accuracy from "./pages/Accuracy";
import Decision from "./pages/Decision";
import Methodology from "./pages/Methodology";
import Revisions from "./pages/Revisions";

const TABS = ["Decision view", "Forecast accuracy", "Forecast revisions", "Methodology"];

export default function App() {
  const [tab, setTab] = useState(0);
  const cutoff = "09:00";
  return (<>
    <header><h1>Wind Day-Ahead Desk</h1><p>GB national wind forecast at decision time · January 2026 · times shown in Europe/London</p></header>
    <nav>{TABS.map((t, i) => <button key={t} className={i === tab ? "on" : ""} onClick={() => setTab(i)}>{t}</button>)}</nav>
    <main>
      {tab === 0 && <Decision cutoffDefault={cutoff} />}
      {tab === 1 && <Accuracy cutoffDefault={cutoff} />}
      {tab === 2 && <Revisions />}
      {tab === 3 && <Methodology />}
    </main>
    <footer>Contains BMRS data © Elexon</footer>
  </>);
}
