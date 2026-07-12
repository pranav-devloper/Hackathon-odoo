import { Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth, ProtectedRoute, AdminRoute } from "./auth";
import Home from "./pages/Home";
import Signup from "./pages/Signup";
import VerifyEmail from "./pages/VerifyEmail";
import Login from "./pages/Login";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Profile from "./pages/Profile";
import Dashboard from "./pages/Dashboard";
import Assets from "./pages/Assets";
import Allocations from "./pages/Allocations";
import Bookings from "./pages/Bookings";
import Maintenance from "./pages/Maintenance";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Placeholder from "./pages/Placeholder";
import Admin from "./pages/Admin";
import NotFound from "./pages/NotFound";

// Routes that render their own full-screen shell (no global nav / centered card).
const FULL_BLEED = ["/dashboard", "/assets", "/allocations", "/bookings", "/maintenance", "/reports", "/settings"];

function Nav() {
  const { isAuthed, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <nav className="nav">
      <Link to="/" className="nav-brand">AssetFlow</Link>
      <div className="nav-links">
        {!isAuthed && (
          <>
            <Link to="/login">Login</Link>
            <Link to="/signup">Sign up</Link>
          </>
        )}
        {isAuthed && (
          <>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/profile">Profile</Link>
            {isAdmin && <Link to="/admin">Admin</Link>}
            <button className="nav-btn" onClick={onLogout}>Logout</button>
          </>
        )}
      </div>
    </nav>
  );
}

const routes = (
  <Routes>
    <Route path="/" element={<Home />} />
    <Route path="/signup" element={<Signup />} />
    <Route path="/verify" element={<VerifyEmail />} />
    <Route path="/login" element={<Login />} />
    <Route path="/forgot-password" element={<ForgotPassword />} />
    <Route path="/reset-password" element={<ResetPassword />} />
    <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
    <Route path="/assets" element={<ProtectedRoute><Assets /></ProtectedRoute>} />
    <Route path="/allocations" element={<ProtectedRoute><Allocations /></ProtectedRoute>} />
    <Route path="/bookings" element={<ProtectedRoute><Bookings /></ProtectedRoute>} />
    <Route path="/maintenance" element={<ProtectedRoute><Maintenance /></ProtectedRoute>} />
    <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
    <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
    <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
    <Route path="/admin" element={<AdminRoute><Admin /></AdminRoute>} />
    <Route path="*" element={<NotFound />} />
  </Routes>
);

export default function App() {
  const location = useLocation();
  const fullBleed = FULL_BLEED.some((p) => location.pathname.startsWith(p));

  if (fullBleed) return routes;

  return (
    <>
      <Nav />
      <main className="container">{routes}</main>
    </>
  );
}
