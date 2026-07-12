import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { api } from "../api";

export default function ResetPassword() {
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || "");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.resetPassword({ email, code, new_password: newPassword });
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h1>Reset password</h1>
      <form onSubmit={submit}>
        <input type="email" placeholder="email@test.com" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        <input type="text" placeholder="Reset code" value={code}
          onChange={(e) => setCode(e.target.value)} required />
        <input type="password" placeholder="New password (min 6)" value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)} required minLength={6} />
        {error && <p className="error">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {busy ? "Resetting…" : "Reset password"}
        </button>
      </form>
      <p className="muted"><Link to="/login">Back to login</Link></p>
    </div>
  );
}
