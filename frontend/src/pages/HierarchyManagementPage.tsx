import { useEffect, useMemo, useState, type FormEvent } from "react";
import api from "../services/api";

type Entity = "colleges" | "departments" | "laboratories" | "rooms";
type LabType = "WET" | "DRY" | "COMPUTING" | "WORKSHOP";

interface College {
  id: string;
  name: string;
  code: string;
  created_at: string;
}

interface Department {
  id: string;
  college_id: string;
  college_name: string;
  name: string;
  code: string;
  created_at: string;
}

interface Laboratory {
  id: string;
  department_id: string;
  department_name: string;
  college_name: string;
  name: string;
  lab_type: LabType;
  manager_id: string | null;
  manager_name: string | null;
  created_at: string;
}

interface Room {
  id: string;
  laboratory_id: string;
  laboratory_name: string;
  department_name: string;
  college_name: string;
  room_number: string;
  building_name: string;
  created_at: string;
}

type OrganizationRecord = College | Department | Laboratory | Room;
interface PageResult<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface UserOption {
  id: string;
  full_name: string;
  is_active: boolean;
}

interface Field {
  key: string;
  label: string;
  kind?: "select";
  required?: boolean;
  options?: { value: string; label: string }[];
}

const entityLabels: Record<Entity, string> = {
  colleges: "Colleges",
  departments: "Departments",
  laboratories: "Laboratories",
  rooms: "Rooms",
};
const entitySingular: Record<Entity, string> = {
  colleges: "College",
  departments: "Department",
  laboratories: "Laboratory",
  rooms: "Room",
};

const columns: Record<Entity, { key: string; label: string }[]> = {
  colleges: [
    { key: "name", label: "College name" },
    { key: "code", label: "Code" },
  ],
  departments: [
    { key: "name", label: "Department" },
    { key: "code", label: "Code" },
    { key: "college_name", label: "College" },
  ],
  laboratories: [
    { key: "name", label: "Laboratory" },
    { key: "lab_type", label: "Type" },
    { key: "department_name", label: "Department" },
    { key: "college_name", label: "College" },
    { key: "manager_name", label: "Manager" },
  ],
  rooms: [
    { key: "room_number", label: "Room" },
    { key: "building_name", label: "Building" },
    { key: "laboratory_name", label: "Laboratory" },
    { key: "department_name", label: "Department" },
    { key: "college_name", label: "College" },
  ],
};

const labTypes: LabType[] = ["WET", "DRY", "COMPUTING", "WORKSHOP"];

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

async function loadAll<T>(
  path: string,
  params: Record<string, string> = {},
): Promise<T[]> {
  const first = await api.get<PageResult<T>>(path, {
    params: { page: 1, size: 100, ...params },
  });
  const items = [...first.data.items];
  for (let page = 2; page <= first.data.pages; page += 1) {
    const response = await api.get<PageResult<T>>(path, {
      params: { page, size: 100, ...params },
    });
    items.push(...response.data.items);
  }
  return items;
}

function cellValue(record: OrganizationRecord, key: string): string {
  const value = Object.entries(record).find(([name]) => name === key)?.[1];
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

export default function HierarchyManagementPage() {
  const [entity, setEntity] = useState<Entity>("colleges");
  const [records, setRecords] = useState<OrganizationRecord[]>([]);
  const [colleges, setColleges] = useState<College[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [laboratories, setLaboratories] = useState<Laboratory[]>([]);
  const [managers, setManagers] = useState<UserOption[]>([]);
  const [form, setForm] = useState<Record<string, string>>({});
  const [editingId, setEditingId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [labTypeFilter, setLabTypeFilter] = useState<LabType | "">("");
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [reload, setReload] = useState(0);
  const [optionsLoading, setOptionsLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const departmentOptions = useMemo(
    () =>
      departments.map((department) => ({
        value: department.id,
        label: `${department.name} (${department.college_name})`,
      })),
    [departments],
  );
  const laboratoryOptions = useMemo(
    () =>
      laboratories.map((laboratory) => ({
        value: laboratory.id,
        label: `${laboratory.name} (${laboratory.department_name})`,
      })),
    [laboratories],
  );

  useEffect(() => {
    let active = true;
    async function fetchOptions() {
      setOptionsLoading(true);
      try {
        const [collegeItems, departmentItems, laboratoryItems, userPage] =
          await Promise.all([
            loadAll<College>("/api/v1/hierarchy/colleges"),
            loadAll<Department>("/api/v1/hierarchy/departments"),
            loadAll<Laboratory>("/api/v1/hierarchy/laboratories"),
            loadAll<UserOption>("/api/v1/users", { role: "LAB_MANAGER" }),
          ]);
        if (active) {
          setColleges(collegeItems);
          setDepartments(departmentItems);
          setLaboratories(laboratoryItems);
          setManagers(userPage.filter((user) => user.is_active));
        }
      } catch (loadError) {
        if (active) setError(errorText(loadError));
      } finally {
        if (active) setOptionsLoading(false);
      }
    }
    void fetchOptions();
    return () => {
      active = false;
    };
  }, [reload]);

  useEffect(() => {
    let active = true;
    async function fetchRecords() {
      setLoading(true);
      const params: Record<string, string | number> = {
        page,
        size: 20,
      };
      if (search.trim()) params.search = search.trim();
      if (filter) {
        if (entity === "departments") params.college_id = filter;
        if (entity === "laboratories") params.department_id = filter;
        if (entity === "rooms") params.laboratory_id = filter;
      }
      if (entity === "laboratories" && labTypeFilter) {
        params.lab_type = labTypeFilter;
      }
      try {
        const response = await api.get<PageResult<OrganizationRecord>>(
          `/api/v1/hierarchy/${entity}`,
          { params },
        );
        if (active) {
          setRecords(response.data.items);
          setPages(response.data.pages);
          setTotal(response.data.total);
          setError("");
        }
      } catch (loadError) {
        if (active) setError(errorText(loadError));
      } finally {
        if (active) setLoading(false);
      }
    }
    void fetchRecords();
    return () => {
      active = false;
    };
  }, [entity, filter, labTypeFilter, page, reload, search]);

  function fieldsFor(activeEntity: Entity): Field[] {
    if (activeEntity === "colleges") {
      return [
        { key: "name", label: "College name", required: true },
        { key: "code", label: "College code", required: true },
      ];
    }
    if (activeEntity === "departments") {
      return [
        {
          key: "college_id",
          label: "College",
          kind: "select",
          required: true,
          options: colleges.map((item) => ({
            value: item.id,
            label: `${item.name} (${item.code})`,
          })),
        },
        { key: "name", label: "Department name", required: true },
        { key: "code", label: "Department code", required: true },
      ];
    }
    if (activeEntity === "laboratories") {
      return [
        {
          key: "department_id",
          label: "Department",
          kind: "select",
          required: true,
          options: departmentOptions,
        },
        { key: "name", label: "Laboratory name", required: true },
        {
          key: "lab_type",
          label: "Laboratory type",
          kind: "select",
          required: true,
          options: labTypes.map((value) => ({ value, label: value })),
        },
        {
          key: "manager_id",
          label: "Designated Lab Manager (optional)",
          kind: "select",
          options: managers.map((manager) => ({
            value: manager.id,
            label: manager.full_name,
          })),
        },
      ];
    }
    return [
      {
        key: "laboratory_id",
        label: "Laboratory",
        kind: "select",
        required: true,
        options: laboratoryOptions,
      },
      { key: "room_number", label: "Room number", required: true },
      { key: "building_name", label: "Building name", required: true },
    ];
  }

  const fields = fieldsFor(entity);

  function selectEntity(next: Entity) {
    setEntity(next);
    setForm({});
    setEditingId(null);
    setSearch("");
    setFilter("");
    setLabTypeFilter("");
    setPage(1);
    setError("");
    setNotice("");
  }

  function startEdit(record: OrganizationRecord) {
    const nextForm: Record<string, string> = {};
    for (const field of fields) {
      const value = Object.entries(record).find(([key]) => key === field.key)?.[1];
      nextForm[field.key] = value == null ? "" : String(value);
    }
    setForm(nextForm);
    setEditingId(record.id);
    setError("");
    setNotice("");
  }

  function cancelEdit() {
    setForm({});
    setEditingId(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    const payload: Record<string, string | null> = {};
    for (const field of fields) {
      const value = form[field.key]?.trim() ?? "";
      payload[field.key] = field.key === "manager_id" && !value ? null : value;
    }
    try {
      if (editingId) {
        await api.patch(`/api/v1/hierarchy/${entity}/${editingId}`, payload);
        setNotice(`${entitySingular[entity]} updated.`);
      } else {
        await api.post(`/api/v1/hierarchy/${entity}`, payload);
        setNotice(`${entitySingular[entity]} created.`);
      }
      cancelEdit();
      setReload((current) => current + 1);
    } catch (saveError) {
      setError(errorText(saveError));
    } finally {
      setSaving(false);
    }
  }

  async function deleteRecord(record: OrganizationRecord) {
    const label =
      entity === "rooms"
        ? cellValue(record, "room_number")
        : cellValue(record, "name");
    if (
      !window.confirm(
        `Delete "${label}"? Records referenced by child or asset data cannot be deleted.`,
      )
    ) {
      return;
    }
    setError("");
    setNotice("");
    try {
      await api.delete(`/api/v1/hierarchy/${entity}/${record.id}`);
      setNotice(`${entitySingular[entity]} deleted.`);
      setReload((current) => current + 1);
    } catch (deleteError) {
      setError(errorText(deleteError));
    }
  }

  const filterLabel =
    entity === "departments"
      ? "College"
      : entity === "laboratories"
        ? "Department"
        : "Laboratory";
  const filterOptions =
    entity === "departments"
      ? colleges.map((item) => ({ value: item.id, label: item.name }))
      : entity === "laboratories"
        ? departmentOptions
        : laboratoryOptions;
  const allFilterLabel =
    entity === "departments"
      ? "All colleges"
      : entity === "laboratories"
        ? "All departments"
        : "All laboratories";
  const showFilter = entity !== "colleges";

  return (
    <section className="space-y-7">
      <header>
        <p className="text-sm font-semibold uppercase tracking-wide text-university-700">
          System administration
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Organizational structure
        </h1>
        <p className="mt-2 max-w-3xl text-slate-600">
          Maintain the approved college, department, laboratory, and room hierarchy.
          Physical location is represented by a laboratory and its rooms.
        </p>
      </header>

      <div
        className="flex flex-wrap gap-2 border-b border-slate-200"
        role="tablist"
        aria-label="Organizational entity"
      >
        {(Object.keys(entityLabels) as Entity[]).map((item) => (
          <button
            key={item}
            id={`tab-${item}`}
            type="button"
            role="tab"
            aria-selected={entity === item}
            aria-controls="hierarchy-panel"
            onClick={() => selectEntity(item)}
            className={`rounded-t-md px-4 py-2 text-sm font-medium ${
              entity === item
                ? "border-b-2 border-university-700 text-university-800"
                : "text-slate-600 hover:bg-white"
            }`}
          >
            {entityLabels[item]}
          </button>
        ))}
      </div>

      <div
        id="hierarchy-panel"
        role="tabpanel"
        aria-labelledby={`tab-${entity}`}
        className="space-y-6"
      >
        <form
          onSubmit={handleSubmit}
          className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 md:grid-cols-2"
        >
          <div className="md:col-span-2">
            <h2 className="text-lg font-semibold">
              {editingId ? `Edit ${entitySingular[entity]}` : `Add ${entitySingular[entity]}`}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {entity === "departments" &&
                "Department codes must be unique within their college."}
              {entity === "rooms" &&
                "Room numbers must be unique within their laboratory."}
              {entity === "laboratories" &&
                "Select the approved laboratory type; an assigned manager is optional."}
            </p>
          </div>
          {fields.map((field) => (
            <label key={field.key} className="text-sm font-medium text-slate-700">
              {field.label}
              {field.kind === "select" ? (
                <select
                  required={field.required}
                  value={form[field.key] ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      [field.key]: event.target.value,
                    }))
                  }
                  className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2"
                >
                  <option value="">
                    {field.key === "manager_id" ? "No designated manager" : "Select…"}
                  </option>
                  {field.options?.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  required={field.required}
                  maxLength={
                    field.key === "code"
                      ? 20
                      : field.key === "room_number"
                        ? 50
                        : 150
                  }
                  value={form[field.key] ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      [field.key]: event.target.value,
                    }))
                  }
                  className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2"
                />
              )}
            </label>
          ))}
          <div className="flex items-center gap-3 md:col-span-2">
            <button
              type="submit"
              disabled={saving || optionsLoading}
              className="rounded-md bg-university-800 px-4 py-2 font-semibold text-white disabled:opacity-60"
            >
              {saving ? "Saving…" : editingId ? "Save changes" : "Create"}
            </button>
            {editingId && (
              <button type="button" onClick={cancelEdit} className="text-sm underline">
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="flex-1 text-sm font-medium text-slate-700">
            Search {entityLabels[entity].toLowerCase()}
            <input
              type="search"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2"
            />
          </label>
          {showFilter && (
            <label className="sm:w-72 text-sm font-medium text-slate-700">
              Filter by {filterLabel.toLowerCase()}
              <select
                value={filter}
                onChange={(event) => {
                  setFilter(event.target.value);
                  setPage(1);
                }}
                className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">
                  {allFilterLabel}
                </option>
                {filterOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          {entity === "laboratories" && (
            <label className="sm:w-56 text-sm font-medium text-slate-700">
              Filter by type
              <select
                value={labTypeFilter}
                onChange={(event) => {
                  setLabTypeFilter(event.target.value as LabType | "");
                  setPage(1);
                }}
                className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">All laboratory types</option>
                {labTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>

        {notice && (
          <p role="status" className="rounded-md bg-green-50 p-3 text-sm text-green-800">
            {notice}
          </p>
        )}
        {error && (
          <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800">
            {error}
          </p>
        )}

        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                {columns[entity].map((column) => (
                  <th key={column.key} scope="col" className="px-4 py-3 font-semibold">
                    {column.label}
                  </th>
                ))}
                <th scope="col" className="px-4 py-3 font-semibold">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={columns[entity].length + 1} className="px-4 py-8 text-center text-slate-600">
                    Loading organizational records…
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={columns[entity].length + 1} className="px-4 py-8 text-center text-slate-600">
                    No matching records.
                  </td>
                </tr>
              ) : (
                records.map((record) => (
                  <tr key={record.id}>
                    {columns[entity].map((column) => (
                      <td key={column.key} className="whitespace-nowrap px-4 py-3 text-slate-800">
                        {cellValue(record, column.key)}
                      </td>
                    ))}
                    <td className="whitespace-nowrap px-4 py-3">
                      <div className="flex gap-3">
                        <button
                          type="button"
                          onClick={() => startEdit(record)}
                          className="font-medium text-university-700 hover:underline"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => void deleteRecord(record)}
                          className="font-medium text-red-700 hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between text-sm text-slate-600">
          <span>
            {total === 0 ? "0 records" : `Showing ${(page - 1) * 20 + 1}–${Math.min(page * 20, total)} of ${total}`}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={page <= 1 || loading}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              className="rounded border border-slate-300 px-3 py-1 disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-2 py-1">
              Page {page} of {Math.max(pages, 1)}
            </span>
            <button
              type="button"
              disabled={page >= pages || loading}
              onClick={() => setPage((current) => current + 1)}
              className="rounded border border-slate-300 px-3 py-1 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
