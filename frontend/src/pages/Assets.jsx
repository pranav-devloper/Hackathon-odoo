import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const STATUSES = ["available", "allocated", "reserved", "under_maintenance", "lost", "retired", "disposed"];
const CONDITIONS = ["new", "good", "fair", "poor"];
const STATUS_TONE = {
  available: "ok", allocated: "accent", reserved: "accent",
  under_maintenance: "warn", lost: "danger", retired: "danger", disposed: "danger",
};
const CONDITION_TONE = { new: "ok", good: "accent", fair: "warn", poor: "danger" };

export default function Assets() {
  const { access, user } = useAuth();
  const canManage = user?.role === "asset_manager" || user?.role === "admin";

  const [assets, setAssets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("All");
  const [status, setStatus] = useState("All");
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [detail, setDetail] = useState(null);
  const [showForm, setShowForm] = useState(false);

  // Register form
  const [fName, setFName] = useState("");
  const [fCat, setFCat] = useState("");
  const [fSerial, setFSerial] = useState("");
  const [fDate, setFDate] = useState("");
  const [fCost, setFCost] = useState("");
  const [fCondition, setFCondition] = useState("new");
  const [fLocation, setFLocation] = useState("");
  const [fBookable, setFBookable] = useState(false);

  const loadAssets = async () => {
    try {
      const params = {};
      if (category !== "All") params.category_id = category;
      if (status !== "All") params.status = status;
      if (query.trim()) params.search = query.trim();
      setAssets(await api.assets.list(params, access));
    } catch (e) { setNotice(e.message); }
  };

  useEffect(() => {
    api.categories.list(access).then(setCategories).catch((e) => setNotice(e.message));
  }, [access]);

  useEffect(() => { loadAssets(); /* eslint-disable-next-line */ }, [category, status, query, access]);

  const saveAsset = async (e) => {
    e.preventDefault();
    if (!fName.trim() || !fCat) return;
    try {
      await api.assets.create({
        name: fName.trim(),
        category_id: Number(fCat),
        serial_number: fSerial.trim() || null,
        acquisition_date: fDate || null,
        acquisition_cost: fCost ? Number(fCost) : null,
        condition: fCondition,
        location: fLocation.trim() || null,
        is_bookable: fBookable,
      }, access);
      setNotice("Asset registered.");
      setFName(""); setFSerial(""); setFDate(""); setFCost(""); setFLocation(""); setFBookable(false);
      setShowForm(false);
      loadAssets();
    } catch (e) { setNotice(e.message); }
  };

  const exportCsv = () => {
    const header = ["Asset Tag", "Name", "Category", "Status", "Location"];
    const rows = assets.map((a) => [a.asset_tag, a.name, a.category_name, a.lifecycle_status, a.location]);
    const csv = [header, ...rows]
      .map((r) => r.map((c) => `"${String(c ?? "").replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url; link.download = "assets.csv"; link.click();
    URL.revokeObjectURL(url);
  };

  const openDetail = async (id) => {
    try { setDetail(await api.assets.get(id, access)); }
    catch (e) { setNotice(e.message); }
  };

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Asset Inventory</h1>
        {canManage && (
          <button className="btn" onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Close" : "+ Register"}
          </button>
        )}
      </div>

      {!canManage && (
        <p className="notice">You can view assets. Only Asset Managers or Admins can register new assets.</p>
      )}
      {notice && <p className="notice">{notice}</p>}

      {showForm && canManage && (
        <section className="panel">
          <h2>Register Asset</h2>
          <form onSubmit={saveAsset} className="register-grid">
            <div className="field"><label>Name</label><input value={fName} onChange={(e) => setFName(e.target.value)} required /></div>
            <div className="field"><label>Category</label>
              <select value={fCat} onChange={(e) => setFCat(e.target.value)} required>
                <option value="">— Select —</option>
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field"><label>Serial Number</label><input value={fSerial} onChange={(e) => setFSerial(e.target.value)} /></div>
            <div className="field"><label>Acquisition Date</label><input type="date" value={fDate} onChange={(e) => setFDate(e.target.value)} /></div>
            <div className="field"><label>Acquisition Cost</label><input type="number" step="0.01" value={fCost} onChange={(e) => setFCost(e.target.value)} /></div>
            <div className="field"><label>Condition</label>
              <select value={fCondition} onChange={(e) => setFCondition(e.target.value)}>
                {CONDITIONS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="field"><label>Location</label><input value={fLocation} onChange={(e) => setFLocation(e.target.value)} /></div>
            <div className="field"><label>Bookable (shared)</label>
              <label className="radio"><input type="checkbox" checked={fBookable} onChange={(e) => setFBookable(e.target.checked)} /> Yes</label>
            </div>
            <button className="btn" type="submit">Save Asset</button>
          </form>
        </section>
      )}

      <section className="panel">
        <div className="asset-toolbar">
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {["All", ...categories.map((c) => c.name)].map((c) => (
              <option key={c} value={c}>{c === "All" ? "Category: All" : c}</option>
            ))}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {["All", ...STATUSES].map((s) => (
              <option key={s} value={s}>{s === "All" ? "Status: All" : s}</option>
            ))}
          </select>
          <input className="asset-search" type="search" placeholder="Search tag, name, serial, location…"
            value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="btn ghost" onClick={exportCsv}>Export</button>
        </div>

        <div className="table-wrap">
          <table className="asset-table">
            <thead>
              <tr><th>Asset Tag</th><th>Name</th><th>Category</th><th>Status</th><th>Location</th><th>Action</th></tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr key={a.id}>
                  <td>{a.asset_tag}</td>
                  <td>{a.name}</td>
                  <td>{a.category_name}</td>
                  <td><span className={"pill " + (STATUS_TONE[a.lifecycle_status] || "accent")}>{a.lifecycle_status}</span></td>
                  <td>{a.location}</td>
                  <td><button className="link-btn" onClick={() => openDetail(a.id)}>View</button></td>
                </tr>
              ))}
              {assets.length === 0 && <tr><td colSpan={6} className="empty">No assets match your filters.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      {detail && (
        <div className="modal-overlay" onClick={() => setDetail(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h2>{detail.asset.name} <span className="muted">({detail.asset.asset_tag})</span></h2>
              <button className="link-btn" onClick={() => setDetail(null)}>Close</button>
            </div>
            <dl className="kv">
              <dt>Category</dt><dd>{detail.asset.category_name}</dd>
              <dt>Status</dt><dd>{detail.asset.lifecycle_status}</dd>
              <dt>Condition</dt><dd>{detail.asset.condition}</dd>
              <dt>Location</dt><dd>{detail.asset.location || "—"}</dd>
              <dt>Serial</dt><dd>{detail.asset.serial_number || "—"}</dd>
              <dt>Bookable</dt><dd>{detail.asset.is_bookable ? "Yes" : "No"}</dd>
            </dl>
            <h3>Allocation History</h3>
            {detail.allocation_history.length === 0 ? <p className="muted">No allocations yet.</p> : (
              <ul className="hist">{detail.allocation_history.map((h) => (
                <li key={h.id}>{h.holder_name || ("User #" + h.holder_user_id)} — {h.status}{h.expected_return_date ? " (due " + h.expected_return_date + ")" : ""}</li>
              ))}</ul>
            )}
            <h3>Maintenance History</h3>
            {detail.maintenance_history.length === 0 ? <p className="muted">No maintenance records yet.</p> : (
              <ul className="hist">{detail.maintenance_history.map((m) => (
                <li key={m.id}>[{m.priority}] {m.issue} — {m.status}</li>
              ))}</ul>
            )}
          </div>
        </div>
      )}
    </DashLayout>
  );
}
