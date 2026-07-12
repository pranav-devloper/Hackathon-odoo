import { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../auth";
import { api } from "../api";

export default function Profile() {
  const { access, user, logout } = useAuth();
  const [profile, setProfile] = useState(user);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    api
      .me(access)
      .then((u) => active && setProfile(u))
      .catch((err) => active && setError(err.message));
    return () => {
      active = false;
    };
  }, [access]);

  const onLogout = async () => {
    setBusy(true);
    await logout();
    navigate("/login");
  };

  return (
    <div className="card">
      <h1>Your profile</h1>
      {error && <p className="error">{error}</p>}
      {profile && (
        <>
          <dl className="kv">
            <dt>ID</dt><dd>{profile.id}</dd>
            <dt>Email</dt><dd>{profile.email}</dd>
            <dt>Name</dt><dd>{profile.full_name}</dd>
            <dt>Role</dt><dd>{profile.role}</dd>
            <dt>Verified</dt><dd>{profile.is_verified ? "yes" : "no"}</dd>
            <dt>Active</dt><dd>{profile.is_active ? "yes" : "no"}</dd>
            <dt>Created</dt><dd>{profile.created_at || "—"}</dd>
          </dl>
          {!profile.is_verified && (
            <p className="notice">
              Your email isn't verified yet.{" "}
              <Link className="footer-link" to="/verify" state={{ email: profile.email }}>
                Verify Email
              </Link>
            </p>
          )}
        </>
      )}
      <div className="row">
        <Link className="btn" to="/dashboard">Back to Dashboard</Link>
        <button className="btn" onClick={onLogout} disabled={busy}>
          {busy ? "Logging out…" : "Logout"}
        </button>
      </div>
    </div>
  );
}
