import { useEffect, useState, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const PRIORITIES = ["low", "medium", "high", "urgent"];
const STATUSES = ["pending", "in_progress", "resolved", "rejected"];
const PRIORITY_TONE = { low: "ok", medium: "accent", high: "warn", urgent: "danger" };
const STATUS_TONE = { pending: "accent", in_progress: "warn", resolved: "ok", rejected: "danger" };
const CHIPS = ["All", "pending", "in_progress", "resolved", "rejected"];

const MANAGER_ROLES = ["asset_manager", "department_head", "admin"];

export default function Maintenance() {
  const { access, user } = useAuth();
  const isManager = MANAGER_ROLES.includes(user?.role);
  const [searchParams] = useSearchParams();

  const [tickets, setTickets] = useState([]);
  const [assets, setAssets] = useState([]);
  const [chip, setChip] = useState("All");
  const [priority, setPriority] = useState("All");
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  // Raise form
  const [showForm, setShowForm] = useState(false);
  const [fAsset, setFAsset] = useState("");
  const [fIssue, setFIssue] = useState("");
  const [fPriority, setFPriority] = useState("medium");

  // Manager update modal
  const [editing, setEditing] = useState(null);

  const load = async () => {
    try {
      const params = isManager ? {} : { mine: true };
      setTickets(await api.maintenance.list(params, access));
    } catch (e) { setNotice(e.message); }
  };

  useEffect(() => {
    load();
    api.assets.list({}, access).then(setAssets).catch(() => {});
    if (searchParams.get("new") === "1") setShowForm(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [access]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return tickets.filter((t) => {
      if (chip !== "All" && t.status !== chip) return false;
      if (priority !== "All" && t.priority !== priority) return false;
      if (q && !`${t.asset_tag} ${t.asset_name} ${t.issue} ${t.assigned_tech || ""}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [tickets, chip, priority, query]);

  const submit = async (e) => {
    e.preventDefault();
    if (!fAsset || !fIssue.trim()) return;
    setLoading(true);
    try {
      await api.maintenance.create(
        { asset_id: Number(fAsset), issue: fIssue.trim(), priority: fPriority },
        access,
      );
      setNotice("Maintenance request raised.");
      setFAsset(""); setFIssue(""); setFPriority("medium");
      setShowForm(false);
      load();
    } catch (e) { setNotice(e.message); }
    finally { setLoading(false); }
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const body = {
        status: editing.status,
        priority: editing.priority,
        assigned_tech: editing.assigned_tech || null,
        resolution: editing.resolution || null,
      };
      await api.maintenance.update(editing.id, body, access);
      setNotice("Ticket updated.");
      setEditing(null);
      load();
    } catch (e) { setNotice(e.message); }
    finally { setLoading(false); }
  };

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Maintenance Requests</h1>
        <button className="btn" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "+ Raise Request"}
        </button>
      </div>

      {notice && <p className="notice">{notice}</p>}

      {showForm && (
        <section className="panel">
          <h2>Raise a Maintenance Request</h2>
          <form onSubmit={submit} className="register-grid">
            <div className="field">
              <label>Asset</label>
              <select value={fAsset} onChange={(e) => setFAsset(e.target.value)} required>
                <option value="">— Select —</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Priority</label>
              <select value={fPriority} onChange={(e) => setFPriority(e.target.value)}>
                {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div className="field" style={{ gridColumn: "1 / -1" }}>
              <label>Issue</label>
              <textarea value={fIssue} onChange={(e) => setFIssue(e.target.value)} placeholder="Describe the fault…" required />
            </div>
            <button className="btn" type="submit" disabled={loading}>
              {loading ? "Submitting…" : "Submit Request"}
            </button>
          </form>
        </section>
      )}

      <div className="chip-row">
        {CHIPS.map((c) => (
          <button key={c} className={"chip" + (chip === c ? " active" : "")} onClick={() => setChip(c)}>{c}</button>
        ))}
      </div>

      <section className="panel">
        <div className="asset-toolbar">
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="All">Priority: All</option>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <input className="asset-search" type="search" placeholder="Search asset, issue, tech…"
            value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>

        <div className="table-wrap">
          <table className="asset-table">
            <thead>
              <tr><th>Ticket</th><th>Asset</th><th>Issue</th><th>Priority</th><th>Status</th><th>Tech</th><th>Action</th></tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td>#{t.id}</td>
                  <td>{t.asset_tag} · {t.asset_name}</td>
                  <td>{t.issue}</td>
                  <td><span className={"pill " + (PRIORITY_TONE[t.priority] || "accent")}>{t.priority}</span></td>
                  <td><span className={"pill " + (STATUS_TONE[t.status] || "accent")}>{t.status}</span></td>
                  <td>{t.assigned_tech || "—"}</td>
                  <td>
                    {isManager ? (
                      <button className="link-btn" onClick={() => setEditing(t)}>Manage</button>
                    ) : (
                      <span className="muted">{t.reporter_name}</span>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={7} className="empty">No maintenance tickets match your filters.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      {editing && (
        <div className="modal-overlay" onClick={() => setEditing(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h2>Manage Ticket #{editing.id}</h2>
              <button className="link-btn" onClick={() => setEditing(null)}>Close</button>
            </div>
            <form onSubmit={saveEdit} className="register-grid">
              <div className="field">
                <label>Status</label>
                <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value })}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Priority</label>
                <select value={editing.priority} onChange={(e) => setEditing({ ...editing, priority: e.target.value })}>
                  {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Assigned Tech</label>
                <input value={editing.assigned_tech || ""} onChange={(e) => setEditing({ ...editing, assigned_tech: e.target.value })} />
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Resolution</label>
                <textarea value={editing.resolution || ""} onChange={(e) => setEditing({ ...editing, resolution: e.target.value })} />
              </div>
              <button className="btn" type="submit" disabled={loading}>{loading ? "Saving…" : "Save"}</button>
            </form>
          </div>
        </div>
      )}
    </DashLayout>
  );
}
