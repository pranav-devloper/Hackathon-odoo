import { useMemo, useState } from "react";
import DashLayout from "../components/DashLayout";

// Placeholder maintenance tickets — backend is auth-only, so this is static
// sample data ready to be replaced by a GET /maintenance endpoint.
const TICKETS = [
  { id: "MT001", asset: "Server", issue: "Cooling Failure", priority: "High", status: "Open", tech: "Unassigned" },
  { id: "MT002", asset: "Laptop", issue: "Keyboard Issue", priority: "Low", status: "Resolved", tech: "Mike" },
  { id: "MT003", asset: "Printer", issue: "Paper Jam", priority: "Medium", status: "In Progress", tech: "Sam" },
  { id: "MT004", asset: "Router", issue: "Config Error", priority: "Urgent", status: "Open", tech: "Unassigned" },
];

const CHIPS = ["All", "Open", "In Progress", "Urgent", "Resolved"];
const ASSETS = ["All", ...Array.from(new Set(TICKETS.map((t) => t.asset)))];
const PRIORITIES = ["All", ...Array.from(new Set(TICKETS.map((t) => t.priority)))];
const PRIORITY_TONE = { Urgent: "danger", High: "warn", Medium: "accent", Low: "ok" };
const STATUS_TONE = { Open: "accent", "In Progress": "warn", Resolved: "ok" };

export default function Maintenance() {
  const [chip, setChip] = useState("All");
  const [asset, setAsset] = useState("All");
  const [priority, setPriority] = useState("All");
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return TICKETS.filter((t) => {
      if (chip === "Urgent") {
        if (t.priority !== "Urgent") return false;
      } else if (chip !== "All" && t.status !== chip) {
        return false;
      }
      if (asset !== "All" && t.asset !== asset) return false;
      if (priority !== "All" && t.priority !== priority) return false;
      if (q && !`${t.id} ${t.asset} ${t.issue} ${t.tech}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [chip, asset, priority, query]);

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Maintenance Requests</h1>
        <button className="btn" onClick={() => setNotice("Raise Request — coming soon (backend has auth only for now).")}>
          + Raise Request
        </button>
      </div>

      {/* Status chips */}
      <div className="chip-row">
        {CHIPS.map((c) => (
          <button
            key={c}
            className={"chip" + (chip === c ? " active" : "")}
            onClick={() => setChip(c)}
          >
            {c}
          </button>
        ))}
      </div>

      {notice && <p className="notice">{notice}</p>}

      <section className="panel">
        <div className="asset-toolbar">
          <select value={asset} onChange={(e) => setAsset(e.target.value)}>
            {ASSETS.map((a) => <option key={a} value={a}>{a === "All" ? "Asset: All" : a}</option>)}
          </select>
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p === "All" ? "Priority: All" : p}</option>)}
          </select>
          <input
            className="asset-search"
            type="search"
            placeholder="Search ticket, asset, issue, tech…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        <div className="table-wrap">
          <table className="asset-table">
            <thead>
              <tr>
                <th>Ticket</th><th>Asset</th><th>Issue</th>
                <th>Priority</th><th>Status</th><th>Assigned Tech</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td>{t.id}</td>
                  <td>{t.asset}</td>
                  <td>{t.issue}</td>
                  <td><span className={"pill " + (PRIORITY_TONE[t.priority] || "accent")}>{t.priority}</span></td>
                  <td><span className={"pill " + (STATUS_TONE[t.status] || "accent")}>{t.status}</span></td>
                  <td>{t.tech}</td>
                  <td>
                    <button className="link-btn" onClick={() => setNotice(`View ${t.id} — coming soon.`)}>View</button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={7} className="empty">No maintenance tickets match your filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </DashLayout>
  );
}
