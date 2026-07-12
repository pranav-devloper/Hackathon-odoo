import { useMemo, useState } from "react";
import DashLayout from "../components/DashLayout";

// Placeholder bookings — backend is auth-only, so this is static sample data
// ready to be replaced by a GET /bookings endpoint.
const BOOKINGS = [
  { id: "BK-001", resource: "Room A", requester: "John", start: "09:00", end: "10:00", status: "Upcoming" },
  { id: "BK-002", resource: "Van 02", requester: "Alex", start: "10:00", end: "11:00", status: "Booked" },
  { id: "BK-003", resource: "Meeting Room", requester: "Sarah", start: "11:00", end: "12:00", status: "Booked" },
  { id: "BK-004", resource: "Room A", requester: "Tom", start: "14:00", end: "15:30", status: "Completed" },
  { id: "BK-005", resource: "Projector", requester: "Mike", start: "16:00", end: "17:00", status: "Cancelled" },
];

const RESOURCES = ["All", ...Array.from(new Set(BOOKINGS.map((b) => b.resource)))];
const STATUSES = ["All", "Upcoming", "Booked", "Completed", "Cancelled"];
const STATUS_TONE = { Upcoming: "accent", Booked: "ok", Completed: "accent", Cancelled: "danger" };

// Time-slot calendar rows (09:00–17:00).
const SLOTS = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"];

export default function Bookings() {
  const [resource, setResource] = useState("All");
  const [status, setStatus] = useState("All");
  const [query, setQuery] = useState("");
  const [view, setView] = useState("list"); // "list" | "calendar"
  const [notice, setNotice] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return BOOKINGS.filter((b) => {
      if (resource !== "All" && b.resource !== resource) return false;
      if (status !== "All" && b.status !== status) return false;
      if (q && !`${b.id} ${b.resource} ${b.requester}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [resource, status, query]);

  // Which booking occupies each hour slot (first match wins).
  const slotMap = useMemo(() => {
    const map = {};
    SLOTS.forEach((slot) => {
      const hit = BOOKINGS.find(
        (b) => b.status !== "Cancelled" && slot >= b.start && slot < b.end
      );
      map[slot] = hit || null;
    });
    return map;
  }, []);

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Bookings Management</h1>
        <button className="btn" onClick={() => setNotice("New Booking — coming soon (backend has auth only for now).")}>
          + New Booking
        </button>
      </div>

      {notice && <p className="notice">{notice}</p>}

      <section className="panel">
        {/* Toolbar */}
        <div className="asset-toolbar">
          <select value={resource} onChange={(e) => setResource(e.target.value)}>
            {RESOURCES.map((r) => <option key={r} value={r}>{r === "All" ? "Resource: All" : r}</option>)}
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

        {view === "list" ? (
          <div className="table-wrap">
            <table className="asset-table">
              <thead>
                <tr>
                  <th>Booking ID</th><th>Resource</th><th>Requester</th>
                  <th>Start</th><th>End</th><th>Status</th><th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.id}>
                    <td>{b.id}</td>
                    <td>{b.resource}</td>
                    <td>{b.requester}</td>
                    <td>{b.start}</td>
                    <td>{b.end}</td>
                    <td><span className={"pill " + (STATUS_TONE[b.status] || "accent")}>{b.status}</span></td>
                    <td>
                      {b.status === "Upcoming" ? (
                        <>
                          <button className="link-btn" onClick={() => setNotice(`Edit ${b.id} — coming soon.`)}>Edit</button>
                          <button className="link-btn danger" onClick={() => setNotice(`Cancel ${b.id} — coming soon.`)}>Cancel</button>
                        </>
                      ) : (
                        <button className="link-btn" onClick={() => setNotice(`View ${b.id} — coming soon.`)}>View</button>
                      )}
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr><td colSpan={7} className="empty">No bookings match your filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="calendar-view">
            <h2>Calendar View</h2>
            {SLOTS.map((slot) => {
              const b = slotMap[slot];
              return (
                <div key={slot} className="cal-row">
                  <span className="cal-time">{slot}</span>
                  {b ? (
                    <div className="cal-bar" title={`${b.resource} · ${b.requester}`}>
                      {b.resource}
                    </div>
                  ) : (
                    <div className="cal-free">Available</div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </DashLayout>
  );
}
