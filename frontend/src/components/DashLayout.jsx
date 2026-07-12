import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Assets", to: "/assets" },
  { label: "Bookings", to: "/bookings" },
  { label: "Maintenance", to: "/maintenance" },
  { label: "Reports", to: "/reports" },
  { label: "Settings", to: "/settings" },
];

// Shared app shell (top bar + sidebar) used by every authenticated page.
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
      <header className="dash-topbar">
        <div className="dash-logo">AssetFlow</div>
        <div className="dash-search">
          <input type="search" placeholder="Search assets, bookings, people…" />
        </div>
        <div className="dash-topbar-right">
          <button className="icon-btn" title="Notifications">
            <span className="bell">🔔</span>
            <span className="badge">3</span>
          </button>
          <button className="profile-chip" onClick={() => navigate("/profile")}>
            <span className="avatar">{initial}</span>
            <span className="profile-name">{user?.full_name || user?.email || "Profile"}</span>
          </button>
        </div>
      </header>

      <div className="dash-body">
        <aside className="dash-sidebar">
          <nav>
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
          <button className="side-link logout" onClick={onLogout}>Logout</button>
        </aside>

        <main className="dash-main">{children}</main>
      </div>
    </div>
  );
}
