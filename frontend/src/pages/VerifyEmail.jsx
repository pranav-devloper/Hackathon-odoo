import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { api } from "../api";

export default function VerifyEmail() {
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || "");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.verifyEmail({ email, code });
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h1>Verify email</h1>
      <p className="muted">Enter the OTP sent to your email (printed in the server console in dev).</p>
      <form onSubmit={submit}>
        <input type="email" placeholder="email@test.com" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        <input type="text" placeholder="6-digit code" value={code}
          onChange={(e) => setCode(e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Verifying…" : "Verify"}
        </button>
      </form>
      <p className="muted"><Link to="/login">Back to login</Link></p>
    </div>
  );
}
