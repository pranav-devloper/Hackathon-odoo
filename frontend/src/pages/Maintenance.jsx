import { useEffect, useMemo, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const CHIPS = ["All", "pending", "approved", "rejected", "in_progress", "resolved"];
const PRIORITIES = ["low", "medium", "high", "urgent"];
const PRIORITY_TONE = { urgent: "danger", high: "warn", medium: "accent", low: "ok" };
const STATUS_TONE = {
  pending: "accent", approved: "warn", rejected: "danger", in_progress: "warn", resolved: "ok",
};

export default function Maintenance() {
  const { access, user } = useAuth();
  const isManager = ["asset_manager", "department_head", "admin"].includes(user?.role);

  const [tickets, setTickets] = useState([]);
  const [assets, setAssets] = useState([]);
  const [chip, setChip] = useState("All");
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  // Raise-request form
  const [showForm, setShowForm] = useState(false);
  const [assetId, setAssetId] = useState("");
  const [issue, setIssue] = useState("");
  const [priority, setPriority] = useState("medium");
  const [photo, setPhoto] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [ts, as] = await Promise.all([
        api.maintenance.list(access),
        api.assets.list({}, access),
      ]);
      setTickets(ts);
      setAssets(as);
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const err = (e) => setNotice(e.message || "Request failed");

  const submit = async (e) => {
    e.preventDefault();
    if (!assetId || !issue.trim()) return;
    setBusy(true);
    try {
      await api.maintenance.create(
        { asset_id: Number(assetId), issue: issue.trim(), priority, photo_path: photo.trim() || null },
        access
      );
      setNotice("Maintenance request raised.");
      setShowForm(false); setAssetId(""); setIssue(""); setPhoto(""); setPriority("medium");
      load();
    } catch (e) { err(e); } finally { setBusy(false); }
  };

  const act = async (id, fn, label) => {
    try { await fn(); setNotice(label); load(); }
    catch (e) { err(e); }
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return tickets.filter((t) => {
      if (chip !== "All" && t.status !== chip) return false;
      if (q && !`${t.id} ${t.asset_tag || ""} ${t.asset_name || ""} ${t.issue} ${t.assigned_tech || ""}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [tickets, chip, query]);

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Maintenance Requests</h1>
        <button className="btn" onClick={() => { setShowForm((v) => !v); setNotice(""); }}>+ Raise Request</button>
      </div>

      {notice && <p className="notice">{notice}</p>}

      {showForm && (
        <section className="panel">
          <h2>Raise Maintenance Request</h2>
          <form onSubmit={submit}>
            <div className="register-grid">
              <div className="field">
                <label>Asset</label>
                <select value={assetId} onChange={(e) => setAssetId(e.target.value)} required>
                  <option value="">— Select asset —</option>
                  {assets.map((a) => (
                    <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Priority</label>
                <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                  {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Issue</label>
                <textarea className="return-notes" value={issue} onChange={(e) => setIssue(e.target.value)} placeholder="Describe the issue…" />
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Photo URL (optional)</label>
                <input value={photo} onChange={(e) => setPhoto(e.target.value)} placeholder="https://…/photo.png" />
              </div>
              <button className="btn" type="submit" disabled={busy}>{busy ? "Submitting…" : "Submit Request"}</button>
            </div>
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
          <input
            className="asset-search"
            type="search"
            placeholder="Search ticket, asset, issue, tech…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {loading && <p className="muted">Loading…</p>}
        <div className="table-wrap">
          <table className="asset-table">
            <thead>
              <tr>
                <th>ID</th><th>Asset</th><th>Issue</th>
                <th>Priority</th><th>Status</th><th>Tech</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.asset_tag ? `${t.asset_tag} · ${t.asset_name || ""}` : (t.asset_name || "—")}</td>
                  <td>{t.issue}</td>
                  <td><span className={"pill " + (PRIORITY_TONE[t.priority] || "accent")}>{t.priority}</span></td>
                  <td><span className={"pill " + (STATUS_TONE[t.status] || "accent")}>{t.status}</span></td>
                  <td>{t.assigned_tech || "—"}</td>
                  <td>
                    {isManager && t.status === "pending" && (
                      <>
                        <button className="link-btn" onClick={() => act(t.id, () => api.maintenance.approve(t.id, access), "Approved.")}>Approve</button>
                        <button className="link-btn danger" onClick={() => act(t.id, () => api.maintenance.reject(t.id, { reason: "" }, access), "Rejected.")}>Reject</button>
                      </>
                    )}
                    {isManager && (t.status === "approved" || t.status === "in_progress") && (
                      <>
                        <button className="link-btn" onClick={() => { const tech = prompt("Assign technician:"); if (tech) act(t.id, () => api.maintenance.assign(t.id, { tech }, access), "Technician assigned."); }}>Assign</button>
                        <button className="link-btn" onClick={() => act(t.id, () => api.maintenance.resolve(t.id, access), "Resolved.")}>Resolve</button>
                      </>
                    )}
                    {!isManager && t.status === "pending" && <span className="muted">Awaiting approval</span>}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && <tr><td colSpan={7} className="empty">No maintenance tickets match your filters.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </DashLayout>
  );
}
