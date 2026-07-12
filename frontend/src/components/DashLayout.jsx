import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import NotificationBell from "./NotificationBell";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Assets", to: "/assets" },
  { label: "Allocations", to: "/allocations" },
  { label: "Bookings", to: "/bookings" },
  { label: "Maintenance", to: "/maintenance" },
  { label: "Audits", to: "/audits" },
  { label: "Reports", to: "/reports" },
  { label: "Activity", to: "/activity" },
  { label: "Settings", to: "/settings" },
];

// Shared app shell: a single vertical sidebar (brand, nav, bell, profile,
// logout) on the left + the page content on the right. Used by every
// authenticated page.
export default function DashLayout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate("/login");
  };

  const initial = (user?.full_name || user?.email || "U")[0].toUpperCase();

  return (
    <div className="dash">
      <aside className="dash-sidebar">
        <div className="dash-brand">AssetFlow</div>

        <div className="dash-search">
          <input type="search" placeholder="Search assets, bookings, people…" />
        </div>

        <nav className="side-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => "side-link" + (isActive ? " active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="side-footer">
          <NotificationBell />
          <button className="profile-chip" onClick={() => navigate("/profile")}>
            <span className="avatar">{initial}</span>
            <span className="profile-name">{user?.full_name || user?.email || "Profile"}</span>
          </button>
          <button className="side-link logout" onClick={onLogout}>Logout</button>
        </div>
      </aside>

      <main className="dash-main">{children}</main>
    </div>
  );
}
