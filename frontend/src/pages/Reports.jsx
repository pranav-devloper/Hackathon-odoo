import { useState } from "react";
import DashLayout from "../components/DashLayout";

// Placeholder analytics — backend is auth-only, so these are static sample
// values ready to be wired to a reporting endpoint later.
const UTILIZATION = [
  { label: "Hardware", pct: 82 },
  { label: "IT", pct: 68 },
  { label: "Software", pct: 55 },
  { label: "Furniture", pct: 40 },
];
const COMPLIANCE = [
  { name: "ISO", ok: true },
  { name: "OSHA", ok: true },
  { name: "GDPR", ok: false },
];
const BOOKING_TREND = [30, 45, 38, 60, 52, 70, 65, 80, 72, 90, 85, 95];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DATE_RANGES = ["Last 7 days", "Last 30 days", "This quarter", "This year"];
const REPORT_TYPES = ["Asset Utilization", "Maintenance Cost", "Booking Trend", "Audit Compliance"];

export default function Reports() {
  const [range, setRange] = useState(DATE_RANGES[1]);
  const [type, setType] = useState(REPORT_TYPES[0]);
  const [notice, setNotice] = useState("");

  const act = (name) => setNotice(`${name} — coming soon (backend has auth only for now).`);
  const maxTrend = Math.max(...BOOKING_TREND);

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Reports</h1>
        <button className="btn" onClick={() => act("Generate Report")}>Generate Report</button>
      </div>

      <section className="panel">
        <div className="asset-toolbar">
          <select value={range} onChange={(e) => setRange(e.target.value)}>
            {DATE_RANGES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {REPORT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <span className="toolbar-spacer" />
          <button className="btn ghost" onClick={() => act("Export PDF")}>Export PDF</button>
          <button className="btn ghost" onClick={() => act("Export Excel")}>Excel</button>
        </div>
      </section>

      {notice && <p className="notice">{notice}</p>}

      {/* Asset Utilization */}
      <section className="panel">
        <h2>Asset Utilization Chart</h2>
        <div className="alloc-chart">
          {UTILIZATION.map((u) => (
            <div key={u.label} className="alloc-row">
              <span className="alloc-label">{u.label}</span>
              <div className="alloc-track">
                <div className="alloc-fill accent" style={{ width: `${u.pct}%` }} />
              </div>
              <span className="alloc-count">{u.pct}%</span>
            </div>
          ))}
        </div>
      </section>

      {/* Audit + Cost */}
      <div className="dash-grid">
        <section className="panel">
          <h2>Audit Compliance</h2>
          <ul className="compliance-list">
            {COMPLIANCE.map((c) => (
              <li key={c.name}>
                <span>{c.name}</span>
                <span className={c.ok ? "check ok" : "check bad"}>{c.ok ? "✔" : "✘"}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="panel">
          <h2>Maintenance Cost</h2>
          <div className="cost-value">₹125,000</div>
          <p className="muted">Planned vs Actual</p>
          <div className="alloc-chart">
            <div className="alloc-row">
              <span className="alloc-label">Planned</span>
              <div className="alloc-track"><div className="alloc-fill ok" style={{ width: "100%" }} /></div>
              <span className="alloc-count">120k</span>
            </div>
            <div className="alloc-row">
              <span className="alloc-label">Actual</span>
              <div className="alloc-track"><div className="alloc-fill warn" style={{ width: "104%" }} /></div>
              <span className="alloc-count">125k</span>
            </div>
          </div>
        </section>
      </div>

      {/* Booking Trend */}
      <section className="panel">
        <h2>Booking Trend Graph</h2>
        <div className="chart-placeholder">
          <div className="bars">
            {BOOKING_TREND.map((v, i) => (
              <div key={i} className="bar" style={{ height: `${(v / maxTrend) * 100}%` }} title={`${MONTHS[i]}: ${v}`} />
            ))}
          </div>
          <div className="bar-labels">
            {MONTHS.map((m) => <span key={m}>{m}</span>)}
          </div>
        </div>
      </section>
    </DashLayout>
  );
}
