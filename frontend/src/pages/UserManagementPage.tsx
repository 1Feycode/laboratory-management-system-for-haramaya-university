import { useEffect, useState, type FormEvent } from "react";
import api from "../services/api";
import type { AppRole, AuthUser } from "../types/auth";

const roles: AppRole[] = [
  "ULMD_ADMIN",
  "MAINTENANCE_TECH",
  "LAB_MANAGER",
  "LAB_TECH",
  "AUDITOR",
];

interface UserPage {
  items: AuthUser[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface DepartmentOption {
  id: string;
  name: string;
  code: string;
}

interface UserForm {
  email: string;
  full_name: string;
  password: string;
  role: AppRole;
  department_id: string;
}

const emptyForm: UserForm = {
  email: "",
  full_name: "",
  password: "",
  role: "AUDITOR",
  department_id: "",
};

function errorText(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "data" in error.response &&
    typeof error.response.data === "object" &&
    error.response.data !== null &&
    "detail" in error.response.data &&
    typeof error.response.data.detail === "string"
  ) {
    return error.response.data.detail;
  }
  return "The request could not be completed. Please try again.";
}

export default function UserManagementPage() {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [form, setForm] = useState<UserForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadUsers() {
    setLoading(true);
    try {
      const [usersResponse, departmentsResponse] = await Promise.all([
        api.get<UserPage>("/api/v1/users", { params: { page: 1, size: 100 } }),
        api.get<DepartmentOption[]>("/api/v1/users/departments"),
      ]);
      setUsers(usersResponse.data.items);
      setDepartments(departmentsResponse.data);
      setError("");
    } catch (loadError) {
      setError(errorText(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, []);

  function changeForm<K extends keyof UserForm>(key: K, value: UserForm[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function beginEdit(user: AuthUser) {
    setEditingId(user.id);
    setForm({
      email: user.email,
      full_name: user.full_name,
      password: "",
      role: user.role,
      department_id: user.department_id ?? "",
    });
    setNotice("");
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    const payload = {
      email: form.email,
      full_name: form.full_name,
      role: form.role,
      department_id: form.department_id || null,
      ...(!editingId ? { password: form.password } : {}),
    };
    try {
      if (editingId) {
        await api.patch(`/api/v1/users/${editingId}`, payload);
        setNotice("User updated.");
      } else {
        await api.post("/api/v1/users", payload);
        setNotice("User account created.");
      }
      cancelEdit();
      await loadUsers();
    } catch (saveError) {
      setError(errorText(saveError));
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(user: AuthUser) {
    setError("");
    setNotice("");
    try {
      await api.patch(`/api/v1/users/${user.id}`, {
        is_active: !user.is_active,
      });
      setNotice(user.is_active ? "User deactivated." : "User activated.");
      await loadUsers();
    } catch (updateError) {
      setError(errorText(updateError));
    }
  }

  return (
    <section className="space-y-8">
      <header>
        <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
          System administration
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">User management</h1>
        <p className="mt-2 text-slate-600">
          Provision institutional accounts and assign one of the five approved roles.
        </p>
      </header>

      <form
        className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 md:grid-cols-2"
        onSubmit={handleSubmit}
      >
        <h2 className="text-lg font-semibold md:col-span-2">
          {editingId ? "Edit user" : "Create user"}
        </h2>
        <label className="text-sm font-medium text-slate-700">
          Full name
          <input
            required
            maxLength={150}
            value={form.full_name}
            onChange={(event) => changeForm("full_name", event.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Institutional email
          <input
            required
            type="email"
            maxLength={255}
            value={form.email}
            onChange={(event) => changeForm("email", event.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        {!editingId && (
          <label className="text-sm font-medium text-slate-700">
            Initial password
            <input
              required
              type="password"
              minLength={10}
              autoComplete="new-password"
              value={form.password}
              onChange={(event) => changeForm("password", event.target.value)}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </label>
        )}
        <label className="text-sm font-medium text-slate-700">
          Role
          <select
            value={form.role}
            onChange={(event) => changeForm("role", event.target.value as AppRole)}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
          >
            {roles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Department (required for Lab Manager and Lab Technician)
          <select
            value={form.department_id}
            onChange={(event) => changeForm("department_id", event.target.value)}
            className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
          >
            <option value="">University-wide / no department</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name} ({department.code})
              </option>
            ))}
            {form.department_id &&
              !departments.some((department) => department.id === form.department_id) && (
                <option value={form.department_id}>{form.department_id}</option>
              )}
          </select>
        </label>
        {departments.length === 0 && (
          <p className="text-sm text-amber-800 md:col-span-2" role="note">
            No departments are configured yet. Add them through the hierarchy stage before
            provisioning department-scoped roles.
          </p>
        )}
        <div className="flex items-center gap-3 md:col-span-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-university-800 px-4 py-2 font-semibold text-white disabled:opacity-60"
          >
            {saving ? "Saving…" : editingId ? "Save changes" : "Create account"}
          </button>
          {editingId && (
            <button type="button" onClick={cancelEdit} className="text-sm underline">
              Cancel
            </button>
          )}
        </div>
      </form>

      {error && <p className="rounded-md bg-rose-50 p-3 text-rose-800" role="alert">{error}</p>}
      {notice && <p className="rounded-md bg-emerald-50 p-3 text-emerald-800" role="status">{notice}</p>}

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <h2 className="p-6 text-lg font-semibold">Provisioned accounts</h2>
        {loading ? (
          <p className="px-6 pb-6 text-slate-600">Loading users…</p>
        ) : users.length === 0 ? (
          <p className="px-6 pb-6 text-slate-600">No user accounts have been provisioned.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-6 py-3">Name / email</th>
                  <th className="px-6 py-3">Role</th>
                  <th className="px-6 py-3">Department</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-900">{user.full_name}</div>
                      <div className="text-slate-600">{user.email}</div>
                    </td>
                    <td className="px-6 py-4">{user.role}</td>
                    <td className="px-6 py-4">{user.department_id ?? "University-wide"}</td>
                    <td className="px-6 py-4">{user.is_active ? "Active" : "Inactive"}</td>
                    <td className="space-x-3 whitespace-nowrap px-6 py-4">
                      <button className="text-university-700 underline" onClick={() => beginEdit(user)}>
                        Edit
                      </button>
                      <button className="text-university-700 underline" onClick={() => void toggleActive(user)}>
                        {user.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}
