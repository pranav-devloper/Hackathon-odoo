import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { api } from "./api";

const AuthContext = createContext(null);
const KEY_ACCESS = "access";
const KEY_REFRESH = "refresh";
const STORES = [localStorage, sessionStorage];

// Read any existing tokens (checked in both storages). "Remember Me" => localStorage
// (survives tab close); unchecked => sessionStorage (cleared when the tab closes).
function loadTokens() {
  let access = "";
  let refresh = "";
  for (const s of STORES) {
    access = s.getItem(KEY_ACCESS) || access;
    refresh = s.getItem(KEY_REFRESH) || refresh;
  }
  return { access, refresh };
}

function persistTokens(tokens, remember) {
  const target = remember ? localStorage : sessionStorage;
  const other = remember ? sessionStorage : localStorage;
  other.removeItem(KEY_ACCESS);
  other.removeItem(KEY_REFRESH);
  target.setItem(KEY_ACCESS, tokens.access_token);
  target.setItem(KEY_REFRESH, tokens.refresh_token);
}

function clearTokens() {
  for (const s of STORES) {
    s.removeItem(KEY_ACCESS);
    s.removeItem(KEY_REFRESH);
  }
}

export function AuthProvider({ children }) {
  const [access, setAccess] = useState(() => loadTokens().access);
  const [refresh, setRefresh] = useState(() => loadTokens().refresh);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On first load, if we have an access token, restore the user profile.
  useEffect(() => {
    let active = true;
    if (!access) {
      setLoading(false);
      return;
    }
    api
      .me(access)
      .then((u) => active && setUser(u))
      .catch(() => {
        if (!active) return;
        // Token invalid/expired: clear it.
        setAccess("");
        setRefresh("");
        localStorage.removeItem(STORAGE.access);
        localStorage.removeItem(STORAGE.refresh);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [access]);

  const login = useCallback((tokens, remember = true) => {
    setAccess(tokens.access_token);
    setRefresh(tokens.refresh_token);
    persistTokens(tokens, remember);
  }, []);

  const logout = useCallback(async () => {
    if (access && refresh) {
      try {
        await api.logout(access, refresh);
      } catch {
        // ignore network errors on logout
      }
    }
    setAccess("");
    setRefresh("");
    setUser(null);
    clearTokens();
  }, [access, refresh]);

  const value = {
    access,
    refresh,
    user,
    loading,
    isAuthed: Boolean(access),
    isAdmin: user?.role === "admin",
    login,
    logout,
    setUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}

// Gate for authenticated routes. While restoring the session we render nothing
// to avoid a flash of the login redirect.
export function ProtectedRoute({ children }) {
  const { isAuthed, loading } = useAuth();
  const location = useLocation();
  if (loading) return null;
  if (!isAuthed) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

// Gate for admin-only routes.
export function AdminRoute({ children }) {
  const { isAuthed, isAdmin, loading } = useAuth();
  if (loading) return null;
  if (!isAuthed) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/profile" replace />;
  return children;
}
