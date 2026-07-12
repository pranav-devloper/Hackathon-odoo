import { useEffect, useState, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const STATUS_TONE = { upcoming: "accent", ongoing: "warn", completed: "ok", cancelled: "danger" };
const STATUSES = ["All", "upcoming", "ongoing", "completed", "cancelled"];

// Day-hour window used by the calendar timeline.
const DAY_START = 7;   // 07:00
const DAY_END = 21;    // 21:00
const DAY_SPAN = DAY_END - DAY_START;

function fmt(dt) {
  if (!dt) return "—";
  const d = new Date(dt);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
function fmtDate(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
function fmtInput(dt) {
  if (!dt) return "";
  const d = new Date(dt);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
// Position helpers for the timeline (percent of the visible day window).
function leftPct(dt) {
  const h = new Date(dt).getHours() + new Date(dt).getMinutes() / 60;
  return Math.max(0, Math.min(100, ((h - DAY_START) / DAY_SPAN) * 100));
}
function widthPct(start, end) {
  const s = new Date(start).getHours() + new Date(start).getMinutes() / 60;
  const e = new Date(end).getHours() + new Date(end).getMinutes() / 60;
  return Math.max(4, Math.min(100, ((e - s) / DAY_SPAN) * 100));
}

export default function Bookings() {
  const { access, user } = useAuth();
  const canManage = ["asset_manager", "department_head", "admin"].includes(user?.role);
  const [searchParams] = useSearchParams();

  const [bookings, setBookings] = useState([]);
  const [assets, setAssets] = useState([]);
  const [resource, setResource] = useState("All");
  const [status, setStatus] = useState("All");
  const [query, setQuery] = useState("");
  const [view, setView] = useState("list");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  // New booking form
  const [showForm, setShowForm] = useState(false);
  const [fAsset, setFAsset] = useState("");
  const [fStart, setFStart] = useState("");
  const [fEnd, setFEnd] = useState("");
  const [fPurpose, setFPurpose] = useState("");

  // Reschedule modal
  const [rescheduling, setRescheduling] = useState(null);
  const [rStart, setRStart] = useState("");
  const [rEnd, setREnd] = useState("");

  const load = async () => {
    try { setBookings(await api.bookings.list({}, access)); }
    catch (e) { setNotice(e.message); }
  };

  useEffect(() => {
    load();
    api.assets.list({}, access).then((a) => setAssets(a.filter((x) => x.is_bookable))).catch(() => {});
    if (searchParams.get("new") === "1") setShowForm(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [access]);

  const bookableAssets = useMemo(() => assets, [assets]);
  const resources = useMemo(
    () => ["All", ...Array.from(new Set(bookings.map((b) => b.asset_name).filter(Boolean)))],
    [bookings]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return bookings
      .filter((b) => resource === "All" || b.asset_name === resource)
      .filter((b) => status === "All" || b.status === status)
      .filter((b) => !q || `${b.id} ${b.asset_name} ${b.user_name}`.toLowerCase().includes(q))
      .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
  }, [bookings, resource, status, query]);

  const submit = async (e) => {
    e.preventDefault();
    if (!fAsset || !fStart || !fEnd) return;
    setLoading(true);
    try {
      await api.bookings.create(
        { asset_id: Number(fAsset), start_time: fStart, end_time: fEnd, purpose: fPurpose || null },
        access,
      );
      setNotice("Booking created.");
      setFAsset(""); setFStart(""); setFEnd(""); setFPurpose("");
      setShowForm(false);
      load();
    } catch (e) { setNotice(e.message); }
    finally { setLoading(false); }
  };

  const doCancel = async (b) => {
    setLoading(true);
    try {
      await api.bookings.cancel(b.id, access);
      setNotice("Booking cancelled.");
      load();
    } catch (e) { setNotice(e.message); }
    finally { setLoading(false); }
  };

  const openReschedule = (b) => {
    setRescheduling(b);
    setRStart(fmtInput(b.start_time));
    setREnd(fmtInput(b.end_time));
  };
  const saveReschedule = async (e) => {
    e.preventDefault();
    if (!rescheduling || !rStart || !rEnd) return;
    setLoading(true);
    try {
      await api.bookings.reschedule(rescheduling.id, { start_time: rStart, end_time: rEnd }, access);
      setNotice("Booking rescheduled.");
      setRescheduling(null);
      load();
    } catch (e) { setNotice(e.message); }
    finally { setLoading(false); }
  };

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Bookings Management</h1>
        <button className="btn" onClick={() => setShowForm((s) => !s)}>
          {showForm ? "Close" : "+ New Booking"}
        </button>
      </div>

      {notice && <p className="notice">{notice}</p>}

      {showForm && (
        <section className="panel">
          <h2>New Booking</h2>
          <form onSubmit={submit} className="register-grid">
            <div className="field">
              <label>Resource (bookable)</label>
              <select value={fAsset} onChange={(e) => setFAsset(e.target.value)} required>
                <option value="">— Select —</option>
                {bookableAssets.map((a) => (
                  <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Start</label>
              <input type="datetime-local" value={fStart} onChange={(e) => setFStart(e.target.value)} required />
            </div>
            <div className="field">
              <label>End</label>
              <input type="datetime-local" value={fEnd} onChange={(e) => setFEnd(e.target.value)} required />
            </div>
            <div className="field" style={{ gridColumn: "1 / -1" }}>
              <label>Purpose</label>
              <input value={fPurpose} onChange={(e) => setFPurpose(e.target.value)} placeholder="e.g. Team sync" />
            </div>
            <button className="btn" type="submit" disabled={loading}>{loading ? "Booking…" : "Book"}</button>
          </form>
        </section>
      )}

      <section className="panel">
        <div className="asset-toolbar">
          <select value={resource} onChange={(e) => setResource(e.target.value)}>
            {resources.map((r) => <option key={r} value={r}>{r === "All" ? "Resource: All" : r}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s === "All" ? "Status: All" : s}</option>)}
          </select>
          <input className="asset-search" type="search" placeholder="Search id, resource, requester…"
            value={query} onChange={(e) => setQuery(e.target.value)} />
          <div className="view-toggle">
            <button className={view === "list" ? "active" : ""} onClick={() => setView("list")}>List</button>
            <button className={view === "calendar" ? "active" : ""} onClick={() => setView("calendar")}>Calendar</button>
          </div>
        </div>

        {view === "list" ? (
          <div className="table-wrap">
            <table className="asset-table">
              <thead>
                <tr><th>ID</th><th>Resource</th><th>Requester</th><th>Start</th><th>End</th><th>Status</th><th>Action</th></tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.id}>
                    <td>#{b.id}</td>
                    <td>{b.asset_tag} · {b.asset_name}</td>
                    <td>{b.user_name}</td>
                    <td>{fmt(b.start_time)}</td>
                    <td>{fmt(b.end_time)}</td>
                    <td><span className={"pill " + (STATUS_TONE[b.status] || "accent")}>{b.status}</span></td>
                    <td>
                      {b.status === "upcoming" && (
                        <>
                          <button className="link-btn" onClick={() => openReschedule(b)}>Reschedule</button>
                          <button className="link-btn danger" onClick={() => doCancel(b)}>Cancel</button>
                        </>
                      )}
                      {b.status !== "upcoming" && <span className="muted">{b.purpose || "—"}</span>}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && <tr><td colSpan={7} className="empty">No bookings match your filters.</td></tr>}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="calendar-view">
            <h2>Calendar {resource !== "All" ? `· ${resource}` : "· all resources"}</h2>
            <div className="cal-axis">
              {Array.from({ length: DAY_SPAN + 1 }, (_, i) => (
                <span key={i} className="cal-tick">{String(DAY_START + i).padStart(2, "0")}:00</span>
              ))}
            </div>
            {filtered
              .filter((b) => b.status !== "cancelled")
              .map((b) => (
                <div key={b.id} className="cal-row">
                  <span className="cal-res">{b.asset_name}</span>
                  <div className="cal-track">
                    <div
                      className={"cal-bar " + (STATUS_TONE[b.status] || "accent")}
                      style={{ left: `${leftPct(b.start_time)}%`, width: `${widthPct(b.start_time, b.end_time)}%` }}
                      title={`${b.user_name}: ${fmt(b.start_time)}–${fmt(b.end_time)}`}
                    >
                      <span className="cal-bar-label">{b.user_name}</span>
                    </div>
                  </div>
                </div>
              ))}
            {filtered.filter((b) => b.status !== "cancelled").length === 0 && (
              <p className="empty">No active bookings to display.</p>
            )}
          </div>
        )}
      </section>

      {rescheduling && (
        <div className="modal-overlay" onClick={() => setRescheduling(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-head">
              <h2>Reschedule #{rescheduling.id}</h2>
              <button className="link-btn" onClick={() => setRescheduling(null)}>Close</button>
            </div>
            <form onSubmit={saveReschedule} className="register-grid">
              <div className="field">
                <label>New Start</label>
                <input type="datetime-local" value={rStart} onChange={(e) => setRStart(e.target.value)} required />
              </div>
              <div className="field">
                <label>New End</label>
                <input type="datetime-local" value={rEnd} onChange={(e) => setREnd(e.target.value)} required />
              </div>
              <button className="btn" type="submit" disabled={loading}>{loading ? "Saving…" : "Reschedule"}</button>
            </form>
          </div>
        </div>
      )}
    </DashLayout>
  );
}
