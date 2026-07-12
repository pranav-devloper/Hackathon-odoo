import { useEffect, useMemo, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const ENTITY_TYPES = ["All", "user", "asset", "allocation", "transfer", "booking", "maintenance", "audit_cycle", "department", "category"];

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new String(iso).replace("T", " ").slice(0, 19);
  return d;
}

export default function Activity() {
  const { access } = useAuth();
  const [logs, setLogs] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [entityType, setEntityType] = useState("All");
  const [action, setAction] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const params = {};
      if (entityType !== "All") params.entity_type = entityType;
      if (action.trim()) params.action = action.trim();
      const [ls, emps] = await Promise.all([
        api.activity.list(params, access),
        api.employees.list(access),
      ]);
      setLogs(ls);
      setEmployees(emps);
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const nameOf = (id) => {
    const e = employees.find((x) => x.id === id);
    return e ? e.full_name : (id ? `user #${id}` : "system");
  };

  const filtered = useMemo(() => logs, [logs]);

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Activity Log</h1>
        <button className="btn ghost" onClick={load}>Refresh</button>
      </div>

      {notice && <p className="notice">{notice}</p>}

      <section className="panel">
        <div className="asset-toolbar">
          <select value={entityType} onChange={(e) => { setEntityType(e.target.value); }}>
            {ENTITY_TYPES.map((t) => <option key={t} value={t}>{t === "All" ? "Entity: All" : t}</option>)}
          </select>
          <input
            className="asset-search"
            type="search"
            placeholder="Filter by action (e.g. asset_allocated)…"
            value={action}
            onChange={(e) => setAction(e.target.value)}
          />
          <button className="btn" onClick={load}>Apply</button>
        </div>

        {loading && <p className="muted">Loading…</p>}
        <div className="table-wrap">
          <table className="asset-table">
            <thead>
              <tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Detail</th></tr>
            </thead>
            <tbody>
              {filtered.map((l) => (
                <tr key={l.id}>
                  <td>{fmtTime(l.created_at)}</td>
                  <td>{nameOf(l.actor_user_id)}</td>
                  <td><span className="pill accent">{l.action}</span></td>
                  <td>{l.entity_type ? `${l.entity_type}${l.entity_id ? " #" + l.entity_id : ""}` : "—"}</td>
                  <td>{l.detail || "—"}</td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={5} className="empty">No activity recorded.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </DashLayout>
  );
}
