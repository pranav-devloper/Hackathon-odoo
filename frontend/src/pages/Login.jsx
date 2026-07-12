import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "../auth";
import { api } from "../api";

export default function Login() {
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || "");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const tokens = await api.login({ email, password });
      login(tokens, remember);
      navigate("/profile");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card login-card">
      <div className="brand-logo">AssetFlow</div>
      <h1 className="login-title">Welcome Back</h1>

      <form onSubmit={submit}>
        <div className="field">
          <label htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <div className="options">
          <label className="remember">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
            />
            Remember Me
          </label>
          <Link to="/forgot-password" className="forgot">Forgot Password?</Link>
        </div>

        {error && <p className="error">{error}</p>}

        <button className="btn login-btn" type="submit" disabled={busy}>
          {busy ? "Logging in…" : "Login"}
        </button>
      </form>

      <p className="login-footer">
        Don't have an account?{" "}
        <Link to="/signup" className="footer-link">Create Employee Account</Link>
      </p>
    </div>
  );
}
