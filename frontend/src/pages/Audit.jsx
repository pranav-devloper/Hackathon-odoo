import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const RESULT_TONE = { verified: "ok", missing: "danger", damaged: "warn" };

export default function Audit() {
  const { access, user } = useAuth();
  const isManager = ["asset_manager", "department_head", "admin"].includes(user?.role);

  const [cycles, setCycles] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  // Create form
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [scopeType, setScopeType] = useState("department");
  const [scopeValue, setScopeValue] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [auditors, setAuditors] = useState([]);
  const [busy, setBusy] = useState(false);

  const loadCycles = async () => {
    setLoading(true);
    try {
      setCycles(await api.audits.list(access));
    } catch (e) { setNotice(e.message); } finally { setLoading(false); }
  };

  useEffect(() => {
    Promise.all([
      api.audits.list(access),
      api.departments.list(access),
      api.employees.list(access),
    ]).then(([cy, depts, emps]) => {
      setCycles(cy); setDepartments(depts); setEmployees(emps); setLoading(false);
    }).catch((e) => { setNotice(e.message); setLoading(false); });
    // eslint-disable-next-line
  }, []);

  const err = (e) => setNotice(e.message || "Request failed");

  const openCycle = async (id) => {
    setOpenId(id);
    try {
      setDetail(await api.audits.get(id, access));
      setNotice("");
    } catch (e) { err(e); }
  };
  const closeDetail = () => { setOpenId(null); setDetail(null); loadCycles(); };

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !scopeValue) return;
    setBusy(true);
    try {
      const cy = await api.audits.create(
        {
          name: name.trim(), scope_type: scopeType, scope_value: String(scopeValue),
          auditors: auditors.map(Number),
          start_date: startDate || null, end_date: endDate || null,
        },
        access
      );
      setNotice(`Audit cycle "${cy.name}" created with ${cy.item_count} asset(s).`);
      setShowForm(false); setName(""); setScopeValue(""); setAuditors([]); setStartDate(""); setEndDate("");
      loadCycles();
    } catch (e) { err(e); } finally { setBusy(false); }
  };

  const mark = async (item, result) => {
    const note = result !== "verified" ? prompt("Note (optional):") : "";
    try {
      await api.audits.markItem(openId, item.id, { result, note: note || null }, access);
      setDetail(await api.audits.get(openId, access));
    } catch (e) { err(e); }
  };

  const closeCycle = async () => {
    if (!confirm("Close this cycle? Missing assets will be marked Lost. This cannot be undone.")) return;
    try {
      await api.audits.close(openId, access);
      setNotice("Audit cycle closed.");
      setDetail(await api.audits.get(openId, access));
    } catch (e) { err(e); }
  };

  const canMark = (cy) =>
    cy.status === "open" && (isManager || (cy.auditors || []).includes(user?.id));

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Asset Audits</h1>
        {isManager && (
          <button className="btn" onClick={() => { setShowForm((v) => !v); setNotice(""); }}>New Audit Cycle</button>
        )}
      </div>

      {notice && <p className="notice">{notice}</p>}

      {isManager && showForm && (
        <section className="panel">
          <h2>New Audit Cycle</h2>
          <form onSubmit={submit}>
            <div className="register-grid">
              <div className="field">
                <label>Cycle Name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Q3 Sweep" required />
              </div>
              <div className="field">
                <label>Scope Type</label>
                <select value={scopeType} onChange={(e) => { setScopeType(e.target.value); setScopeValue(""); }}>
                  <option value="department">Department</option>
                  <option value="location">Location</option>
                </select>
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>{scopeType === "department" ? "Department" : "Location"}</label>
                {scopeType === "department" ? (
                  <select value={scopeValue} onChange={(e) => setScopeValue(e.target.value)} required>
                    <option value="">— Select department —</option>
                    {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                ) : (
                  <input value={scopeValue} onChange={(e) => setScopeValue(e.target.value)} placeholder="e.g. Lab" required />
                )}
              </div>
              <div className="field">
                <label>Start Date</label>
                <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
              </div>
              <div className="field">
                <label>End Date</label>
                <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Auditors (hold Ctrl/Cmd to select multiple)</label>
                <select multiple value={auditors} onChange={(e) => setAuditors(Array.from(e.target.selectedOptions).map((o) => o.value))}>
                  {employees.map((em) => <option key={em.id} value={em.id}>{em.full_name}</option>)}
                </select>
              </div>
              <button className="btn" type="submit" disabled={busy}>{busy ? "Creating…" : "Create Cycle"}</button>
            </div>
          </form>
        </section>
      )}

      {/* Cycle list */}
      <section className="panel">
        <h2>Audit Cycles</h2>
        {loading && <p className="muted">Loading…</p>}
        <div className="table-wrap">
          <table className="asset-table">
            <thead><tr><th>ID</th><th>Name</th><th>Scope</th><th>Status</th><th>Items</th><th>Verified</th><th>Action</th></tr></thead>
            <tbody>
              {cycles.map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>{c.name}</td>
                  <td>{c.scope_type}: {c.scope_value}</td>
                  <td><span className={"pill " + (c.status === "open" ? "accent" : "ok")}>{c.status}</span></td>
                  <td>{c.item_count}</td>
                  <td>{c.verified_count}</td>
                  <td>
                    <button className="link-btn" onClick={() => openCycle(c.id)}>
                      {openId === c.id ? "Close" : "Open"}
                    </button>
                  </td>
                </tr>
              ))}
              {cycles.length === 0 && <tr><td colSpan={7} className="empty">No audit cycles yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      {/* Cycle detail */}
      {detail && (
        <section className="panel">
          <div className="page-head">
            <h2>{detail.cycle.name} — Items</h2>
            {detail.cycle.status === "open" && isManager && (
              <button className="btn" onClick={closeCycle}>Close Cycle</button>
            )}
          </div>
          <p className="muted">
            Scope: {detail.cycle.scope_type} = {detail.cycle.scope_value} · Status: {detail.cycle.status}
          </p>

          <div className="table-wrap">
            <table className="asset-table">
              <thead><tr><th>Asset</th><th>Result</th><th>Note</th><th>Action</th></tr></thead>
              <tbody>
                {detail.items.map((it) => (
                  <tr key={it.id}>
                    <td>{it.asset_tag ? `${it.asset_tag} · ${it.asset_name || ""}` : (it.asset_name || "—")}</td>
                    <td>
                      {it.result
                        ? <span className={"pill " + (RESULT_TONE[it.result] || "accent")}>{it.result}</span>
                        : <span className="muted">pending</span>}
                    </td>
                    <td>{it.note || "—"}</td>
                    <td>
                      {canMark(detail.cycle) ? (
                        <div className="action-list">
                          <button className="link-btn" onClick={() => mark(it, "verified")}>Verify</button>
                          <button className="link-btn danger" onClick={() => mark(it, "missing")}>Missing</button>
                          <button className="link-btn" onClick={() => mark(it, "damaged")}>Damaged</button>
                        </div>
                      ) : <span className="muted">—</span>}
                    </td>
                  </tr>
                ))}
                {detail.items.length === 0 && <tr><td colSpan={4} className="empty">No assets in scope.</td></tr>}
              </tbody>
            </table>
          </div>

          {detail.discrepancies.length > 0 && (
            <div className="panel" style={{ marginTop: "1rem", borderLeft: "4px solid var(--error)" }}>
              <h3>Discrepancy Report ({detail.discrepancies.length})</h3>
              <ul className="critical-list">
                {detail.discrepancies.map((d) => (
                  <li key={d.id}>
                    <span>{d.asset_tag} · {d.asset_name}</span>
                    <span className={"pill " + (RESULT_TONE[d.result] || "accent")}>{d.result}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button className="btn ghost" style={{ marginTop: "1rem" }} onClick={closeDetail}>Back to list</button>
        </section>
      )}
    </DashLayout>
  );
}
