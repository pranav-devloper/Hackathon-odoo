import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const ALLOC_STATUS_TONE = {
  active: "accent",
  returned: "ok",
  overdue: "danger",
};
const TRANSFER_STATUS_TONE = {
  requested: "warn",
  approved: "ok",
  rejected: "danger",
};

function fmtDate(d) {
  if (!d) return "—";
  return String(d).slice(0, 10);
}

export default function Allocations() {
  const { access, user } = useAuth();
  const canManage =
    user?.role === "asset_manager" || user?.role === "department_head" || user?.role === "admin";

  const [tab, setTab] = useState("allocations");

  // Data
  const [allocations, setAllocations] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [assets, setAssets] = useState([]); // available assets (allocate form)
  const [employees, setEmployees] = useState([]); // holder / recipient picker

  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  // Allocate form
  const [showAllocate, setShowAllocate] = useState(false);
  const [aAsset, setAAsset] = useState("");
  const [aHolder, setAHolder] = useState("");
  const [aReturn, setAReturn] = useState("");

  // Transfer form
  const [showTransfer, setShowTransfer] = useState(false);
  const [tAsset, setTAsset] = useState("");
  const [tTo, setTTo] = useState("");
  const [tReturn, setTReturn] = useState("");
  const [tNote, setTNote] = useState("");

  // Return modal
  const [returning, setReturning] = useState(null);
  const [returnNotes, setReturnNotes] = useState("");

  const loadAllocations = async () => {
    try { setAllocations(await api.allocations.list({ active: false }, access)); }
    catch (e) { setNotice(e.message); }
  };
  const loadTransfers = async () => {
    try { setTransfers(await api.transfers.list({}, access)); }
    catch (e) { setNotice(e.message); }
  };

  useEffect(() => {
    loadAllocations();
    loadTransfers();
    api.assets.list({ status: "available" }, access).then(setAssets).catch(() => {});
    api.employees.list(access).then(setEmployees).catch((e) => setNotice(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [access]);

  // ---------- Allocate ----------
  const submitAllocate = async (e) => {
    e.preventDefault();
    if (!aAsset || !aHolder) return;
    setLoading(true);
    try {
      await api.allocations.create(
        {
          asset_id: Number(aAsset),
          holder_user_id: Number(aHolder),
          expected_return_date: aReturn || null,
        },
        access,
      );
      setNotice("Asset allocated.");
      setAAsset(""); setAHolder(""); setAReturn("");
      setShowAllocate(false);
      loadAllocations();
      api.assets.list({ status: "available" }, access).then(setAssets).catch(() => {});
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ---------- Return ----------
  const openReturn = (a) => { setReturning(a); setReturnNotes(""); };
  const submitReturn = async (e) => {
    e.preventDefault();
    if (!returning) return;
    setLoading(true);
    try {
      await api.allocations.return(returning.id, { condition_notes: returnNotes || null }, access);
      setNotice(`Returned ${returning.asset_tag || returning.asset_name || "asset"}.`);
      setReturning(null);
      loadAllocations();
      api.assets.list({ status: "available" }, access).then(setAssets).catch(() => {});
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ---------- Transfer ----------
  const submitTransfer = async (e) => {
    e.preventDefault();
    if (!tAsset || !tTo) return;
    setLoading(true);
    try {
      await api.transfers.create(
        {
          asset_id: Number(tAsset),
          to_user_id: Number(tTo),
          expected_return_date: tReturn || null,
          note: tNote || null,
        },
        access,
      );
      setNotice("Transfer requested.");
      setTAsset(""); setTTo(""); setTReturn(""); setTNote("");
      setShowTransfer(false);
      loadTransfers();
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  const actTransfer = async (id, action) => {
    setLoading(true);
    try {
      if (action === "approve") await api.transfers.approve(id, access);
      else await api.transfers.reject(id, access);
      setNotice(`Transfer ${action}d.`);
      loadTransfers();
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  const employeeName = (id) =>
    (employees.find((u) => u.id === id)?.full_name) || (id ? `User #${id}` : "—");

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Allocations</h1>
        <div className="head-actions">
          {canManage && (
            <button className="btn" onClick={() => setShowAllocate((s) => !s)}>
              {showAllocate ? "Close" : "＋ Allocate"}
            </button>
          )}
          <button className="btn ghost" onClick={() => setShowTransfer((s) => !s)}>
            {showTransfer ? "Close" : "↔ Request Transfer"}
          </button>
        </div>
      </div>

      {notice && <p className="notice">{notice}</p>}

      {showAllocate && canManage && (
        <section className="panel">
          <h2>Allocate Asset</h2>
          <form onSubmit={submitAllocate} className="register-grid">
            <div className="field">
              <label>Asset (available)</label>
              <select value={aAsset} onChange={(e) => setAAsset(e.target.value)} required>
                <option value="">— Select —</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Holder</label>
              <select value={aHolder} onChange={(e) => setAHolder(e.target.value)} required>
                <option value="">— Select —</option>
                {employees.map((u) => (
                  <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Expected Return Date</label>
              <input type="date" value={aReturn} onChange={(e) => setAReturn(e.target.value)} />
            </div>
            <button className="btn" type="submit" disabled={loading}>
              {loading ? "Allocating…" : "Allocate"}
            </button>
          </form>
        </section>
      )}

      {showTransfer && (
        <section className="panel">
          <h2>Request a Transfer</h2>
          <form onSubmit={submitTransfer} className="register-grid">
            <div className="field">
              <label>Asset</label>
              <select value={tAsset} onChange={(e) => setTAsset(e.target.value)} required>
                <option value="">— Select —</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Transfer to</label>
              <select value={tTo} onChange={(e) => setTTo(e.target.value)} required>
                <option value="">— Select —</option>
                {employees
                  .filter((u) => u.id !== user?.id)
                  .map((u) => (
                    <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                  ))}
              </select>
            </div>
            <div className="field">
              <label>Expected Return Date</label>
              <input type="date" value={tReturn} onChange={(e) => setTReturn(e.target.value)} />
            </div>
            <div className="field" style={{ gridColumn: "1 / -1" }}>
              <label>Note (optional)</label>
              <input value={tNote} onChange={(e) => setTNote(e.target.value)} placeholder="Reason for transfer…" />
            </div>
            <button className="btn" type="submit" disabled={loading}>
              {loading ? "Requesting…" : "Request Transfer"}
            </button>
          </form>
        </section>
      )}

      <div className="tabs">
        <button className={"tab" + (tab === "allocations" ? " active" : "")} onClick={() => setTab("allocations")}>
          Allocations
        </button>
        <button className={"tab" + (tab === "transfers" ? " active" : "")} onClick={() => setTab("transfers")}>
          Transfers
        </button>
      </div>

      {tab === "allocations" && (
        <section className="panel">
          <div className="table-wrap">
            <table className="asset-table">
              <thead>
                <tr>
                  <th>Asset</th><th>Holder</th><th>Expected Return</th>
                  <th>Status</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {allocations.map((a) => (
                  <tr key={a.id}>
                    <td>{a.asset_tag} · {a.asset_name}</td>
                    <td>{a.holder_name || `User #${a.holder_user_id}`}</td>
                    <td>{fmtDate(a.expected_return_date)}</td>
                    <td>
                      <span className={"pill " + (ALLOC_STATUS_TONE[a.status] || "accent")}>
                        {a.status}{a.is_overdue ? " · overdue" : ""}
                      </span>
                    </td>
                    <td>
                      {a.status === "active" && canManage && (
                        <button className="link-btn danger" onClick={() => openReturn(a)}>Return</button>
                      )}
                    </td>
                  </tr>
                ))}
                {allocations.length === 0 && (
                  <tr><td colSpan={5} className="empty">No allocations yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === "transfers" && (
        <section className="panel">
          <div className="table-wrap">
            <table className="asset-table">
              <thead>
                <tr>
                  <th>Asset</th><th>From → To</th><th>Expected Return</th>
                  <th>Status</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {transfers.map((t) => (
                  <tr key={t.id}>
                    <td>{t.asset_tag} · {t.asset_name}</td>
                    <td>{employeeName(t.from_user_id)} → {t.to_name || employeeName(t.to_user_id)}</td>
                    <td>{fmtDate(t.expected_return_date)}</td>
                    <td>
                      <span className={"pill " + (TRANSFER_STATUS_TONE[t.status] || "accent")}>{t.status}</span>
                    </td>
                    <td>
                      {t.status === "requested" && canManage && (
                        <>
                          <button className="link-btn" onClick={() => actTransfer(t.id, "approve")} disabled={loading}>Approve</button>
                          <button className="link-btn danger" onClick={() => actTransfer(t.id, "reject")} disabled={loading}>Reject</button>
                        </>
                      )}
                      {t.status !== "pending" && t.note && (
                        <span className="muted" title={t.note}>has note</span>
                      )}
                    </td>
                  </tr>
                ))}
                {transfers.length === 0 && (
                  <tr><td colSpan={5} className="empty">No transfers yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {returning && (
        <div className="modal-overlay" onClick={() => setReturning(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h2>Return {returning.asset_tag} · {returning.asset_name}</h2>
              <button className="link-btn" onClick={() => setReturning(null)}>Close</button>
            </div>
            <form onSubmit={submitReturn}>
              <div className="field">
                <label>Condition Notes (optional)</label>
                <textarea
                  className="return-notes"
                  value={returnNotes}
                  onChange={(e) => setReturnNotes(e.target.value)}
                  placeholder="e.g. minor scratch on casing"
                />
              </div>
              <button className="btn" type="submit" disabled={loading}>
                {loading ? "Returning…" : "Confirm Return"}
              </button>
            </form>
          </div>
        </div>
      )}
    </DashLayout>
  );
}
