import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

// KPI cards driven by GET /dashboard (real data).
const KPI_DEFS = [
  { key: "assets_available", label: "Assets Available", tone: "ok" },
  { key: "assets_allocated", label: "Assets Allocated", tone: "accent" },
  { key: "under_maintenance", label: "Under Maintenance", tone: "warn" },
  { key: "active_bookings", label: "Active Bookings", tone: "accent" },
  { key: "pending_transfers", label: "Pending Transfers", tone: "warn" },
  { key: "upcoming_returns", label: "Upcoming Returns", tone: "ok" },
];

const CRITICAL = [
  { label: "Overdue Returns", count: 0, tone: "danger" },
  { label: "Pending Transfers", count: 0, tone: "warn" },
  { label: "Upcoming Returns", count: 0, tone: "accent" },
];

export default function Dashboard() {
  const { access, user } = useAuth();
  const [kpis, setKpis] = useState(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    let active = true;
    api.dashboard(access)
      .then((d) => active && setKpis(d))
      .catch((e) => active && setStatus(e.message));
    return () => { active = false; };
  }, [access]);

  const act = (name) => setStatus(`${name} — coming soon (backend has auth only for now).`);

  return (
    <DashLayout>
      {/* KPI cards (real data) */}
      <section className="stat-row">
        {kpis
          ? KPI_DEFS.map((k) => (
              <div key={k.key} className={"stat-card " + k.tone}>
                <div className="stat-value">{kpis[k.key] ?? 0}</div>
                <div className="stat-label">{k.label}</div>
              </div>
            ))
          : <div className="stat-card"><div className="stat-value">…</div><div className="stat-label">Loading…</div></div>}
      </section>

      {kpis && kpis.overdue_returns > 0 && (
        <p className="notice">
          {kpis.overdue_returns} asset(s) are past their Expected Return Date — flagged as overdue.
        </p>
      )}

      {status && <p className="notice">{status}</p>}

      <div className="dash-grid">
        {/* Quick Actions */}
        <section className="panel">
          <h2>Quick Actions</h2>
          <div className="action-list">
            <button className="btn" onClick={() => act("Register Asset")}>Register Asset</button>
            <button className="btn" onClick={() => act("Book Resource")}>Book Resource</button>
            <button className="btn" onClick={() => act("Raise Maintenance Request")}>Maintenance</button>
          </div>
        </section>

        {/* Critical Actions (overdue/pending from KPIs) */}
        <section className="panel">
          <h2>Critical Actions</h2>
          <ul className="critical-list">
            <li onClick={() => act("Overdue Returns")}>
              <span>Overdue Returns</span>
              <span className={"pill " + (kpis && kpis.overdue_returns > 0 ? "danger" : "accent")}>
                {kpis ? kpis.overdue_returns : 0}
              </span>
            </li>
            <li onClick={() => act("Pending Transfers")}>
              <span>Pending Transfers</span>
              <span className={"pill " + (kpis && kpis.pending_transfers > 0 ? "warn" : "accent")}>
                {kpis ? kpis.pending_transfers : 0}
              </span>
            </li>
            <li onClick={() => act("Upcoming Returns")}>
              <span>Upcoming Returns</span>
              <span className="pill accent">{kpis ? kpis.upcoming_returns : 0}</span>
            </li>
          </ul>
        </section>
      </div>

      {/* Timeline / charts */}
      <section className="panel">
        <h2>Resource Timeline / Charts</h2>
        <div className="chart-placeholder">
          <div className="bars">
            {[40, 65, 30, 80, 55, 70, 45].map((h, i) => (
              <div key={i} className="bar" style={{ height: `${h}%` }} />
            ))}
          </div>
          <p className="muted">Sample data — connect a reporting endpoint to render live charts.</p>
        </div>
      </section>
    </DashLayout>
  );
}
