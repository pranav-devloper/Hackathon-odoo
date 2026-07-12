import { useEffect, useState } from "react";
import DashLayout from "../components/DashLayout";
import { useAuth } from "../auth";
import { api } from "../api";

const TABS = ["Departments", "Asset Categories", "Employee Directory"];
const ROLE_LABELS = {
  user: "Employee",
  department_head: "Department Head",
  asset_manager: "Asset Manager",
  admin: "Admin",
};
const ROLE_OPTIONS = ["user", "department_head", "asset_manager", "admin"];

export default function Settings() {
  const { access, user } = useAuth();
  const [tab, setTab] = useState("Departments");

  const [departments, setDepartments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  // Department form
  const [dName, setDName] = useState("");
  const [dHead, setDHead] = useState("");
  const [dParent, setDParent] = useState("");
  const [dStatus, setDStatus] = useState("active");

  // Category form
  const [cName, setCName] = useState("");
  const [cWarranty, setCWarranty] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [depts, cats, emps] = await Promise.all([
        api.departments.list(access),
        api.categories.list(access),
        api.employees.list(access),
      ]);
      setDepartments(depts);
      setCategories(cats);
      setEmployees(emps);
    } catch (e) {
      setNotice(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const err = (e) => setNotice(e.message || "Request failed");

  // ---------- Department actions ----------
  const saveDepartment = async (e) => {
    e.preventDefault();
    if (!dName.trim()) return;
    try {
      await api.departments.create(
        { name: dName.trim(), head_id: dHead ? Number(dHead) : null, parent_id: dParent ? Number(dParent) : null, status: dStatus },
        access
      );
      setNotice(`Department "${dName.trim()}" created.`);
      setDName(""); setDHead(""); setDParent(""); setDStatus("active");
      load();
    } catch (e) { err(e); }
  };

  const toggleDeptStatus = async (dept) => {
    try {
      await api.departments.update(dept.id, { status: dept.status === "active" ? "inactive" : "active" }, access);
      load();
    } catch (e) { err(e); }
  };

  // ---------- Category actions ----------
  const saveCategory = async (e) => {
    e.preventDefault();
    if (!cName.trim()) return;
    try {
      await api.categories.create(
        { name: cName.trim(), warranty_period_days: cWarranty ? Number(cWarranty) : null },
        access
      );
      setNotice(`Category "${cName.trim()}" created.`);
      setCName(""); setCWarranty("");
      load();
    } catch (e) { err(e); }
  };

  // ---------- Employee actions ----------
  const updateEmployee = async (id, patch, emp) => {
    try {
      await api.employees.update(id, patch, access);
      setEmployees((prev) => prev.map((x) => (x.id === id ? { ...x, ...patch } : x)));
    } catch (e) { err(e); }
  };

  return (
    <DashLayout>
      <div className="page-head">
        <h1>Organization Setup</h1>
        <span className="role-badge">{ROLE_LABELS[user?.role] || user?.role || "User"}</span>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t} className={"tab" + (tab === t ? " active" : "")} onClick={() => { setTab(t); setNotice(""); }}>
            {t}
          </button>
        ))}
      </div>

      {notice && <p className="notice">{notice}</p>}
      {loading && <p className="muted">Loading…</p>}

      {tab === "Departments" && (
        <>
          <section className="panel">
            <h2>Department Management</h2>
            <form onSubmit={saveDepartment}>
              <div className="field">
                <label>Department Name</label>
                <input value={dName} onChange={(e) => setDName(e.target.value)} placeholder="e.g. Finance" required />
              </div>
              <div className="field">
                <label>Department Head</label>
                <select value={dHead} onChange={(e) => setDHead(e.target.value)}>
                  <option value="">— None —</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>{emp.full_name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Parent Department</label>
                <select value={dParent} onChange={(e) => setDParent(e.target.value)}>
                  <option value="">— None —</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Status</label>
                <div className="radio-row">
                  <label className="radio">
                    <input type="radio" name="dstatus" checked={dStatus === "active"} onChange={() => setDStatus("active")} /> Active
                  </label>
                  <label className="radio">
                    <input type="radio" name="dstatus" checked={dStatus === "inactive"} onChange={() => setDStatus("inactive")} /> Inactive
                  </label>
                </div>
              </div>
              <button className="btn" type="submit">Save Department</button>
            </form>
          </section>

          <section className="panel">
            <h2>Department List</h2>
            <div className="table-wrap">
              <table className="asset-table">
                <thead><tr><th>ID</th><th>Name</th><th>Head</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>
                  {departments.map((d) => (
                    <tr key={d.id}>
                      <td>{d.id}</td>
                      <td>{d.name}</td>
                      <td>{d.head_name || "—"}</td>
                      <td><span className={"pill " + (d.status === "active" ? "ok" : "danger")}>{d.status}</span></td>
                      <td>
                        <button className="link-btn" onClick={() => toggleDeptStatus(d)}>
                          {d.status === "active" ? "Deactivate" : "Activate"}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {departments.length === 0 && <tr><td colSpan={5} className="empty">No departments yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {tab === "Asset Categories" && (
        <>
          <section className="panel">
            <h2>Add Category</h2>
            <form onSubmit={saveCategory} className="asset-toolbar">
              <input className="asset-search" value={cName} onChange={(e) => setCName(e.target.value)} placeholder="Category name…" required />
              <input
                style={{ maxWidth: 160 }}
                type="number" min="0"
                value={cWarranty} onChange={(e) => setCWarranty(e.target.value)}
                placeholder="Warranty (days)"
              />
              <button className="btn" type="submit">Add</button>
            </form>
          </section>
          <section className="panel">
            <h2>Asset Categories</h2>
            <div className="table-wrap">
              <table className="asset-table">
                <thead><tr><th>ID</th><th>Name</th><th>Warranty</th></tr></thead>
                <tbody>
                  {categories.map((c) => (
                    <tr key={c.id}><td>{c.id}</td><td>{c.name}</td><td>{c.warranty_period_days ? c.warranty_period_days + " days" : "—"}</td></tr>
                  ))}
                  {categories.length === 0 && <tr><td colSpan={3} className="empty">No categories yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {tab === "Employee Directory" && (
        <section className="panel">
          <h2>Employee Directory</h2>
          <p className="muted">This is the only place roles are assigned — promote an employee to Department Head or Asset Manager here.</p>
          <div className="table-wrap">
            <table className="asset-table">
              <thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Role</th><th>Status</th></tr></thead>
              <tbody>
                {employees.map((emp) => (
                  <tr key={emp.id}>
                    <td>{emp.id}</td>
                    <td>{emp.full_name}</td>
                    <td>
                      <select
                        value={emp.department_id ?? ""}
                        onChange={(e) => updateEmployee(emp.id, { department_id: e.target.value ? Number(e.target.value) : null }, emp)}
                      >
                        <option value="">— None —</option>
                        {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                      </select>
                    </td>
                    <td>
                      <select
                        value={emp.role}
                        onChange={(e) => updateEmployee(emp.id, { role: e.target.value }, emp)}
                      >
                        {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                      </select>
                    </td>
                    <td>
                      <span className={"pill " + (emp.is_active ? "ok" : "danger")}>{emp.is_active ? "Active" : "Inactive"}</span>
                      <button className="link-btn" style={{ marginLeft: 10 }} onClick={() => updateEmployee(emp.id, { is_active: !emp.is_active }, emp)}>
                        {emp.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
                {employees.length === 0 && <tr><td colSpan={5} className="empty">No employees yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </DashLayout>
  );
}
