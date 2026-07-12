import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import { api } from "../api";

export default function Admin() {
  const { access } = useAuth();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api
      .adminMe(access)
      .then((u) => active && setData(u))
      .catch((err) => active && setError(err.message));
    return () => {
      active = false;
    };
  }, [access]);

  return (
    <div className="card">
      <h1>Admin</h1>
      <p className="muted">Admin-only area (requires the <code>admin</code> role).</p>
      {error && <p className="error">{error}</p>}
      {data && (
        <dl className="kv">
          <dt>ID</dt><dd>{data.id}</dd>
          <dt>Email</dt><dd>{data.email}</dd>
          <dt>Name</dt><dd>{data.full_name}</dd>
          <dt>Role</dt><dd>{data.role}</dd>
        </dl>
      )}
    </div>
  );
}
