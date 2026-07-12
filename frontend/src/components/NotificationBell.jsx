import { useEffect, useRef, useState } from "react";
import { useAuth } from "../auth";
import { api } from "../api";

const TYPE_ICON = {
  overdue_return: "⏰",
  allocation: "📦",
  return_confirmed: "↩️",
  transfer_request: "🔁",
  transfer_approved: "✅",
  transfer_rejected: "⛔",
};

// Global notifications bell: live unread count + dropdown panel.
// Mounted once inside DashLayout so it's visible on every authenticated page.
export default function NotificationBell() {
  const { access } = useAuth();
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const ref = useRef(null);

  const fetchNotifs = async () => {
    try {
      setLoading(true);
      setItems(await api.notifications.list(access));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Load unread count on mount so the badge is correct even before opening.
  useEffect(() => {
    if (access) fetchNotifs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [access]);

  // Close the dropdown on outside click.
  useEffect(() => {
    if (!open) return;
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const unread = items.filter((n) => !n.is_read).length;

  const onMarkRead = async (id) => {
    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    try { await api.notifications.read(id, access); } catch { /* ignore */ }
  };

  const onMarkAll = async () => {
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
    try { await api.notifications.readAll(access); } catch { /* ignore */ }
  };

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) fetchNotifs();
  };

  return (
    <div className="bell-wrap" ref={ref}>
      <button className="icon-btn" title="Notifications" onClick={toggle}>
        <span className="bell">🔔</span>
        {unread > 0 && (
          <span className="badge">{unread > 99 ? "99+" : unread}</span>
        )}
      </button>

      {open && (
        <div className="notif-panel">
          <div className="notif-head">
            <span>Notifications</span>
            {unread > 0 && (
              <button className="link-btn" onClick={onMarkAll}>Mark all read</button>
            )}
          </div>
          {error && <p className="notif-error">{error}</p>}
          {loading && items.length === 0 ? (
            <p className="notif-empty muted">Loading…</p>
          ) : items.length === 0 ? (
            <p className="notif-empty muted">You're all caught up 🎉</p>
          ) : (
            <ul className="notif-list">
              {items.map((n) => (
                <li
                  key={n.id}
                  className={"notif-item" + (n.is_read ? " read" : " unread")}
                  onClick={() => !n.is_read && onMarkRead(n.id)}
                >
                  <span className="notif-icon">{TYPE_ICON[n.type] || "🔔"}</span>
                  <div className="notif-body">
                    <p className="notif-msg">{n.message}</p>
                    <span className="notif-time muted">
                      {new Date(n.created_at).toLocaleString()}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
