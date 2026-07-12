import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setMsg("");
    setBusy(true);
    try {
      const res = await api.forgotPassword({ email });
      setMsg(res.message || "If the email exists, a reset code has been sent.");
      navigate("/reset-password", { state: { email } });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h1>Forgot password</h1>
      <p className="muted">We'll send a reset code to your email.</p>
      <form onSubmit={submit}>
        <input type="email" placeholder="email@test.com" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        {msg && <p className="success">{msg}</p>}
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Sending…" : "Send reset code"}
        </button>
      </form>
      <p className="muted"><Link to="/login">Back to login</Link></p>
    </div>
  );
}
