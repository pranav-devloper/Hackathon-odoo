import { useEffect, useMemo, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const STATUSES = ["All", "upcoming", "completed", "cancelled"];
const STATUS_TONE = { upcoming: "accent", completed: "ok", cancelled: "danger" };
const SLOTS = [
  "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00",
];

function fmt(iso) {
  if (!iso) return "—";
  return String(iso).slice(11, 16); // HH:MM
}
function fmtDate(iso) {
  if (!iso) return "";
  return String(iso).slice(0, 10);
}

export default function Bookings() {
  const { access, user } = useAuth();

  const [bookings, setBookings] = useState([]);
  const [assets, setAssets] = useState([]);
  const [resource, setResource] = useState("All");
  const [status, setStatus] = useState("All");
  const [query, setQuery] = useState("");
  const [view, setView] = useState("list");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  // New-booking form
  const [showForm, setShowForm] = useState(false);
  const [assetId, setAssetId] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [purpose, setPurpose] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [bk, as] = await Promise.all([
        api.bookings.list({}, access),
        api.assets.list({}, access),
      ]);
      setBookings(bk);
      setAssets(as);
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const err = (e) => setNotice(e.message || "Request failed");

  // Only bookable assets can be reserved.
  const bookableAssets = useMemo(() => assets.filter((a) => a.is_bookable), [assets]);

  const withSeconds = (v) => (v && v.length === 16 ? v + ":00" : v);

  const submit = async (e) => {
    e.preventDefault();
    if (!assetId || !start || !end) return;
    setBusy(true);
    try {
      await api.bookings.create(
        { asset_id: Number(assetId), start_time: withSeconds(start), end_time: withSeconds(end), purpose: purpose.trim() || null },
        access
      );
      setNotice("Booking created.");
      setShowForm(false); setAssetId(""); setStart(""); setEnd(""); setPurpose("");
      load();
    } catch (e) { err(e); } finally { setBusy(false); }
  };

  const cancel = async (b) => {
    try {
      await api.bookings.cancel(b.id, access);
      setNotice("Booking cancelled.");
      load();
    } catch (e) { err(e); }
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return bookings.filter((b) => {
      if (resource !== "All" && b.asset_id !== Number(resource)) return false;
      if (status !== "All" && b.status !== status) return false;
      if (q && !`${b.id} ${b.asset_tag || ""} ${b.asset_name || ""} ${b.user_name || ""}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [bookings, resource, status, query]);

  // Calendar: bookings for the selected resource across the day's slots.
  const visible = resource === "All" ? bookings : bookings.filter((b) => b.asset_id === Number(resource));
  const slotMap = useMemo(() => {
    const map = {};
    SLOTS.forEach((slot) => {
      const hh = parseInt(slot.slice(0, 2), 10);
      const hit = visible.find((b) => b.status !== "cancelled" && hh >= parseInt(fmt(b.start_time).slice(0, 2), 10) && hh < parseInt(fmt(b.end_time).slice(0, 2), 10));
      map[slot] = hit || null;
    });
    return map;
  }, [visible]);

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Bookings Management</h1>
        <button className="btn" onClick={() => { setShowForm((v) => !v); setNotice(""); }}>+ New Booking</button>
      </div>

      {notice && <p className="notice">{notice}</p>}

      {showForm && (
        <section className="panel">
          <h2>New Booking</h2>
          <form onSubmit={submit}>
            <div className="register-grid">
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Resource (bookable asset)</label>
                <select value={assetId} onChange={(e) => setAssetId(e.target.value)} required>
                  <option value="">— Select resource —</option>
                  {bookableAssets.map((a) => (
                    <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Start</label>
                <input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} required />
              </div>
              <div className="field">
                <label>End</label>
                <input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} required />
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label>Purpose (optional)</label>
                <input value={purpose} onChange={(e) => setPurpose(e.target.value)} placeholder="e.g. Team sync" />
              </div>
              <button className="btn" type="submit" disabled={busy}>{busy ? "Booking…" : "Book"}</button>
            </div>
          </form>
        </section>
      )}

      <section className="panel">
        <div className="asset-toolbar">
          <select value={resource} onChange={(e) => setResource(e.target.value)}>
            <option value="All">Resource: All</option>
            {assets.map((a) => <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s === "All" ? "Status: All" : s}</option>)}
          </select>
          <input
            className="asset-search"
            type="search"
            placeholder="Search id, resource, requester…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="view-toggle">
            <button className={view === "list" ? "active" : ""} onClick={() => setView("list")}>List</button>
            <button className={view === "calendar" ? "active" : ""} onClick={() => setView("calendar")}>Calendar</button>
          </div>
        </div>

        {loading && <p className="muted">Loading…</p>}

        {view === "list" ? (
          <div className="table-wrap">
            <table className="asset-table">
              <thead>
                <tr>
                  <th>ID</th><th>Resource</th><th>Requester</th>
                  <th>Date</th><th>Start</th><th>End</th><th>Status</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.id}>
                    <td>{b.id}</td>
                    <td>{b.asset_tag ? `${b.asset_tag} · ${b.asset_name || ""}` : (b.asset_name || "—")}</td>
                    <td>{b.user_name || "—"}</td>
                    <td>{fmtDate(b.start_time)}</td>
                    <td>{fmt(b.start_time)}</td>
                    <td>{fmt(b.end_time)}</td>
                    <td><span className={"pill " + (STATUS_TONE[b.status] || "accent")}>{b.status}</span></td>
                    <td>
                      {b.status === "upcoming" ? (
                        (b.user_id === user?.id || ["asset_manager", "department_head", "admin"].includes(user?.role)) ? (
                          <button className="link-btn danger" onClick={() => cancel(b)}>Cancel</button>
                        ) : <span className="muted">—</span>
                      ) : (
                        <span className="muted">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && <tr><td colSpan={8} className="empty">No bookings match your filters.</td></tr>}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="calendar-view">
            <h2>Calendar View {resource !== "All" ? `(selected resource)` : `(all resources)`}</h2>
            {SLOTS.map((slot) => {
              const b = slotMap[slot];
              return (
                <div key={slot} className="cal-row">
                  <span className="cal-time">{slot}</span>
                  {b ? (
                    <div className="cal-bar" title={`${b.asset_name || b.asset_tag} · ${b.user_name || ""}`}>
                      {b.asset_tag || b.asset_name}
                    </div>
                  ) : (
                    <div className="cal-free">Available</div>
                  )}
                </div>
              );
            })}
            {visible.length === 0 && <p className="muted">No bookings for this view.</p>}
          </div>
        )}
      </section>
    </DashLayout>
  );
}
