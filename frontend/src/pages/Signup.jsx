import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.signup({ email, full_name: fullName, password });
      navigate("/");
    } catch (err) {
      // Email already registered -> send the user to log in instead.
      const detail = err.data?.detail;
      if (typeof detail === "string" && /already registered/i.test(detail)) {
        navigate("/login", { state: { email } });
        return;
      }
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h1>Create Employee Account</h1>
      <p className="muted">A 6-digit verification code is printed in the server console.</p>
      <form onSubmit={submit}>
        <input type="email" placeholder="email@test.com" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        <input type="text" placeholder="Full name" value={fullName}
          onChange={(e) => setFullName(e.target.value)} required />
        <input type="password" placeholder="Password (min 6)" value={password}
          onChange={(e) => setPassword(e.target.value)} required minLength={6} />
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Creating…" : "Sign up"}
        </button>
      </form>
      <p className="muted">Already have an account? <Link to="/login">Login</Link></p>
    </div>
  );
}
