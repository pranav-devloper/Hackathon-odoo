// Thin fetch wrapper around the FastAPI /auth/* backend.
// Base URL is "" so the same code works behind the Vite dev proxy (/auth -> :8000)
// and when the built SPA is served same-origin by FastAPI.

async function request(method, path, { body, token } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = "Bearer " + token;

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    // Surface FastAPI's {detail: ...} as an Error message.
    const message =
      (data && (data.detail || data.message)) ||
      `Request failed (${res.status})`;
    const err = new Error(typeof message === "string" ? message : JSON.stringify(message));
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  signup: (payload) => request("POST", "/auth/signup", { body: payload }),
  verifyEmail: (payload) => request("POST", "/auth/verify-email", { body: payload }),
  login: (payload) => request("POST", "/auth/login", { body: payload }),
  forgotPassword: (payload) => request("POST", "/auth/forgot-password", { body: payload }),
  resetPassword: (payload) => request("POST", "/auth/reset-password", { body: payload }),
  me: (token) => request("GET", "/auth/me", { token }),
  adminMe: (token) => request("GET", "/auth/admin/me", { token }),
  logout: (token, refreshToken) =>
    request("POST", "/auth/logout", { token, body: { refresh_token: refreshToken } }),

  // ----- Organization setup (admin) -----
  departments: {
    list: (token) => request("GET", "/org/departments", { token }),
    create: (body, token) => request("POST", "/org/departments", { body, token }),
    update: (id, body, token) => request("PATCH", `/org/departments/${id}`, { body, token }),
  },
  categories: {
    list: (token) => request("GET", "/org/asset-categories", { token }),
    create: (body, token) => request("POST", "/org/asset-categories", { body, token }),
    update: (id, body, token) => request("PATCH", `/org/asset-categories/${id}`, { body, token }),
  },
  employees: {
    list: (token) => request("GET", "/org/employees", { token }),
    update: (id, body, token) => request("PATCH", `/org/employees/${id}`, { body, token }),
  },

  // ----- Assets -----
  assets: {
    list: (params = {}, token) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== "" && v != null) qs.set(k, v);
      });
      const q = qs.toString();
      return request("GET", "/assets" + (q ? "?" + q : ""), { token });
    },
    create: (body, token) => request("POST", "/assets", { body, token }),
    get: (id, token) => request("GET", `/assets/${id}`, { token }),
    update: (id, body, token) => request("PATCH", `/assets/${id}`, { body, token }),
  },

  dashboard: (token) => request("GET", "/dashboard", { token }),

  // ----- Allocations / Returns -----
  allocations: {
    list: (params = {}, token) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== "" && v != null) qs.set(k, v);
      });
      const q = qs.toString();
      return request("GET", "/allocations" + (q ? "?" + q : ""), { token });
    },
    create: (body, token) => request("POST", "/allocations", { body, token }),
    return: (id, body, token) =>
      request("POST", `/allocations/${id}/return`, { body, token }),
  },

  // ----- Transfers -----
  transfers: {
    list: (params = {}, token) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== "" && v != null) qs.set(k, v);
      });
      const q = qs.toString();
      return request("GET", "/transfers" + (q ? "?" + q : ""), { token });
    },
    create: (body, token) => request("POST", "/transfers", { body, token }),
    approve: (id, token) => request("POST", `/transfers/${id}/approve`, { token }),
    reject: (id, token) => request("POST", `/transfers/${id}/reject`, { token }),
  },

  // ----- Notifications -----
  notifications: {
    list: (token) => request("GET", "/notifications", { token }),
    read: (id, token) => request("POST", `/notifications/${id}/read`, { token }),
    readAll: (token) => request("POST", "/notifications/read-all", { token }),
  },

  // ----- Maintenance (Screen 7) -----
  maintenance: {
    list: (token) => request("GET", "/maintenance", { token }),
    create: (body, token) => request("POST", "/maintenance", { body, token }),
    approve: (id, token) => request("POST", `/maintenance/${id}/approve`, { token }),
    reject: (id, body, token) => request("POST", `/maintenance/${id}/reject`, { body, token }),
    assign: (id, body, token) => request("POST", `/maintenance/${id}/assign`, { body, token }),
    resolve: (id, token) => request("POST", `/maintenance/${id}/resolve`, { token }),
  },

  // ----- Audits (Screen 8) -----
  audits: {
    list: (token) => request("GET", "/audits/cycles", { token }),
    get: (id, token) => request("GET", `/audits/cycles/${id}`, { token }),
    create: (body, token) => request("POST", "/audits/cycles", { body, token }),
    updateAuditors: (id, body, token) => request("PATCH", `/audits/cycles/${id}`, { body, token }),
    markItem: (id, itemId, body, token) =>
      request("PATCH", `/audits/cycles/${id}/items/${itemId}`, { body, token }),
    discrepancies: (id, token) => request("GET", `/audits/cycles/${id}/discrepancies`, { token }),
    close: (id, token) => request("POST", `/audits/cycles/${id}/close`, { token }),
  },

  // ----- Reports (Screen 9) -----
  reports: {
    summary: (token) => request("GET", "/reports/summary", { token }),
    exportRaw: async (section, token) => {
      const res = await fetch(`/reports/export?section=${encodeURIComponent(section || "all")}`, {
        headers: token ? { Authorization: "Bearer " + token } : {},
      });
      return await res.text();
    },
  },

  // ----- Activity log (Screen 10) -----
  activity: {
    list: (params = {}, token) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v) qs.set(k, v);
      });
      const q = qs.toString();
      return request("GET", "/activity-logs" + (q ? "?" + q : ""), { token });
    },
  },
};
