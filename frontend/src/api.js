// Thin fetch wrapper around the FastAPI backend.
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

// Multipart upload (asset media). FastAPI expects a form field named "file".
async function upload(path, file, token) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(path, {
    method: "POST",
    headers: token ? { Authorization: "Bearer " + token } : {},
    body: form,
  });
  let data = null;
  try { data = await res.json(); } catch { data = null; }
  if (!res.ok) {
    const message = (data && (data.detail || data.message)) || `Upload failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
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
    upload: (id, file, token) => upload(`/assets/${id}/media`, file, token),
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

  // ----- Bookings (Screen 6) -----
  bookings: {
    list: (params = {}, token) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== "" && v != null) qs.set(k, v);
      });
      const q = qs.toString();
      return request("GET", "/bookings" + (q ? "?" + q : ""), { token });
    },
    create: (body, token) => request("POST", "/bookings", { body, token }),
    get: (id, token) => request("GET", `/bookings/${id}`, { token }),
    reschedule: (id, body, token) =>
      request("PATCH", `/bookings/${id}`, { body, token }),
    cancel: (id, token) => request("POST", `/bookings/${id}/cancel`, { token }),
  },

  // ----- Maintenance (Screen 7) -----
  maintenance: {
    list: (params = {}, token) => {
      const qs = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== "" && v != null) qs.set(k, v);
      });
      const q = qs.toString();
      return request("GET", "/maintenance" + (q ? "?" + q : ""), { token });
    },
    create: (body, token) => request("POST", "/maintenance", { body, token }),
    update: (id, body, token) =>
      request("PATCH", `/maintenance/${id}`, { body, token }),
  },
};
