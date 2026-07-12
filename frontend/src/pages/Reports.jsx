import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const DATE_RANGES = ["Last 7 days", "Last 30 days", "This quarter", "This year"];
const REPORT_TYPES = ["All", "utilization", "maintenance_by_category", "department_allocation", "booking_heatmap", "due_for_maintenance", "near_retirement"];

export default function Reports() {
  const { access } = useAuth();
  const [range, setRange] = useState(DATE_RANGES[1]);
  const [type, setType] = useState("All");
  const [data, setData] = useState(null);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      setData(await api.reports.summary(access));
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const download = async () => {
    try {
      const section = type === "All" ? "all" : type;
      const text = await api.reports.exportRaw(section, access);
      const blob = new Blob([text], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "assetflow-report.csv";
      a.click();
      URL.revokeObjectURL(url);
      setNotice("Report exported.");
    } catch (e) {
      setNotice(e.message || "Export failed");
    }
  };

  const maxAlloc = data ? Math.max(1, ...data.utilization.most_used.map((r) => r.allocations)) : 1;
  const maxDept = data ? Math.max(1, ...data.department_allocation.map((r) => r.allocations)) : 1;
  const maxHeat = data ? Math.max(1, ...data.booking_heatmap.map((h) => h.bookings)) : 1;
  const t = data ? data.totals : {};

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Reports &amp; Analytics</h1>
        <button className="btn" onClick={download}>Export CSV</button>
      </div>

      <section className="panel">
        <div className="asset-toolbar">
          <select value={range} onChange={(e) => setRange(e.target.value)}>
            {DATE_RANGES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {REPORT_TYPES.map((r) => <option key={r} value={r}>{r === "All" ? "Section: All" : r.replace(/_/g, " ")}</option>)}
          </select>
        </div>
      </section>

      {notice && <p className="notice">{notice}</p>}
      {loading && <p className="muted">Loading…</p>}

      {data && (
        <>
          <div className="stat-row">
            <div className="stat-card"><div className="stat-value">{t.assets}</div><div className="stat-label">Total Assets</div></div>
            <div className="stat-card ok"><div className="stat-value">{t.allocations_active}</div><div className="stat-label">Active Allocations</div></div>
            <div className="stat-card accent"><div className="stat-value">{t.bookings_upcoming}</div><div className="stat-label">Upcoming Bookings</div></div>
            <div className="stat-card warn"><div className="stat-value">{t.maintenance_open}</div><div className="stat-label">Open Maintenance</div></div>
          </div>

          {(type === "All" || type === "utilization") && (
            <div className="dash-grid">
              <section className="panel">
                <h2>Most-Used Assets</h2>
                {data.utilization.most_used.length === 0 && <p className="muted">No allocation history yet.</p>}
                <div className="alloc-chart">
                  {data.utilization.most_used.map((r) => (
                    <div key={r.asset_tag} className="alloc-row">
                      <span className="alloc-label">{r.asset_tag}</span>
                      <div className="alloc-track">
                        <div className="alloc-fill accent" style={{ width: `${(r.allocations / maxAlloc) * 100}%` }} />
                      </div>
                      <span className="alloc-count">{r.allocations}</span>
                    </div>
                  ))}
                </div>
                <h3 style={{ marginTop: "1rem" }}>Idle Assets ({data.utilization.idle.length})</h3>
                {data.utilization.idle.length === 0 ? <p className="muted">None.</p> : (
                  <div className="table-wrap">
                    <table className="asset-table">
                      <thead><tr><th>Tag</th><th>Name</th><th>Category</th></tr></thead>
                      <tbody>
                        {data.utilization.idle.slice(0, 12).map((r) => (
                          <tr key={r.asset_tag}><td>{r.asset_tag}</td><td>{r.name}</td><td>{r.category_name || "—"}</td></tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              <section className="panel">
                <h2>Department Allocation</h2>
                {data.department_allocation.length === 0 && <p className="muted">No active allocations.</p>}
                <div className="alloc-chart">
                  {data.department_allocation.map((r) => (
                    <div key={r.department_name} className="alloc-row">
                      <span className="alloc-label">{r.department_name}</span>
                      <div className="alloc-track">
                        <div className="alloc-fill ok" style={{ width: `${(r.allocations / maxDept) * 100}%` }} />
                      </div>
                      <span className="alloc-count">{r.allocations}</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          )}

          {(type === "All" || type === "maintenance_by_category") && (
            <section className="panel">
              <h2>Maintenance by Category</h2>
              <div className="table-wrap">
                <table className="asset-table">
                  <thead><tr><th>Category</th><th>Tickets</th></tr></thead>
                  <tbody>
                    {data.maintenance_by_category.map((r) => (
                      <tr key={r.category_name}><td>{r.category_name}</td><td>{r.tickets}</td></tr>
                    ))}
                    {data.maintenance_by_category.length === 0 && <tr><td colSpan={2} className="empty">No maintenance tickets.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {(type === "All" || type === "booking_heatmap") && (
            <section className="panel">
              <h2>Booking Heatmap (by hour)</h2>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {data.booking_heatmap.filter((h) => h.bookings > 0).map((h) => (
                  <div key={h.hour} title={`${h.hour}:00 — ${h.bookings} bookings`}
                    style={{
                      background: `rgba(99,102,241,${(h.bookings / maxHeat) * 0.9 + 0.1})`,
                      borderRadius: 6, padding: "0.4rem 0.55rem", minWidth: 56, textAlign: "center",
                    }}>
                    <div style={{ fontWeight: 700 }}>{h.bookings}</div>
                    <div className="muted" style={{ fontSize: "0.7rem" }}>{String(h.hour).padStart(2, "0")}:00</div>
                  </div>
                ))}
                {data.booking_heatmap.filter((h) => h.bookings > 0).length === 0 && <p className="muted">No bookings yet.</p>}
              </div>
            </section>
          )}

          {(type === "All" || type === "due_for_maintenance" || type === "near_retirement") && (
            <div className="dash-grid">
              {type === "All" || type === "due_for_maintenance" ? (
                <section className="panel">
                  <h2>Due for Maintenance</h2>
                  <div className="table-wrap">
                    <table className="asset-table">
                      <thead><tr><th>Tag</th><th>Name</th><th>Category</th></tr></thead>
                      <tbody>
                        {data.due_for_maintenance.map((r) => (
                          <tr key={r.asset_tag}><td>{r.asset_tag}</td><td>{r.name}</td><td>{r.category_name || "—"}</td></tr>
                        ))}
                        {data.due_for_maintenance.length === 0 && <tr><td colSpan={3} className="empty">Nothing under maintenance.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : <></>}
              {type === "All" || type === "near_retirement" ? (
                <section className="panel">
                  <h2>Near Retirement</h2>
                  <div className="table-wrap">
                    <table className="asset-table">
                      <thead><tr><th>Tag</th><th>Name</th><th>Condition</th></tr></thead>
                      <tbody>
                        {data.near_retirement.map((r) => (
                          <tr key={r.asset_tag}><td>{r.asset_tag}</td><td>{r.name}</td><td>{r.condition}</td></tr>
                        ))}
                        {data.near_retirement.length === 0 && <tr><td colSpan={3} className="empty">No assets in poor/fair condition.</td></tr>}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : <></>}
            </div>
          )}
        </>
      )}
    </DashLayout>
  );
}
