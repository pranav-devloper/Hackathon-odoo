import { Link } from "react-router-dom";
import { useAuth } from "../auth";

export default function Home() {
  const { isAuthed } = useAuth();
  return (
    <div className="card">
      <h1>AssetFlow</h1>
      <p className="muted">
        Track assets, manage employee accounts, and control access — all
        backed by the FastAPI auth service.
      </p>
      <div className="row">
        {isAuthed ? (
          <Link className="btn" to="/dashboard">Go to dashboard</Link>
        ) : (
          <>
            <Link className="btn" to="/signup">Sign up</Link>
            <Link className="btn" to="/login">Login</Link>
          </>
        )}
      </div>
    </div>
  );
}
