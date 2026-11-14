import { isAxiosError } from "axios";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  createCategory,
  deleteCategory,
  listCategories,
  updateCategory,
  type AssetCategory,
  type Page,
} from "../services/assets";

interface CategoryValues {
  name: string;
  requires_calibration: boolean;
  default_calibration_interval_days: number;
}

const EMPTY: CategoryValues = {
  name: "",
  requires_calibration: false,
  default_calibration_interval_days: 0,
};

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return error instanceof Error ? error.message : "The category request failed.";
}

export default function AssetCategoryPage() {
  const [result, setResult] = useState<Page<AssetCategory>>({
    items: [],
    total: 0,
    page: 1,
    size: 20,
    pages: 0,
  });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [values, setValues] = useState<CategoryValues>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await listCategories(search || undefined, page);
      setResult(data);
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    void loadCategories();
  }, [loadCategories]);

  function beginEdit(category: AssetCategory) {
    setEditingId(category.id);
    setValues({
      name: category.name,
      requires_calibration: category.requires_calibration,
      default_calibration_interval_days: category.default_calibration_interval_days,
    });
    setNotice("");
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      if (editingId) {
        await updateCategory(editingId, values);
        setNotice("Asset category updated.");
      } else {
        await createCategory(values);
        setNotice("Asset category created.");
      }
      setEditingId(null);
      setValues(EMPTY);
      await loadCategories();
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(category: AssetCategory) {
    if (!window.confirm(`Delete category "${category.name}"? Categories used by assets cannot be deleted.`)) {
      return;
    }
    setError("");
    setNotice("");
    try {
      await deleteCategory(category.id);
      setNotice("Asset category deleted.");
      await loadCategories();
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    }
  }

  return (
    <section>
      <Link to="/assets" className="text-sm text-university-700 hover:underline">← Back to assets</Link>
      <h1 className="mt-4 text-3xl font-semibold text-slate-900">Asset categories</h1>
      <p className="mt-2 text-slate-600">
        Maintain the approved category lookup and its calibration requirement metadata.
      </p>
      {error && <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      {notice && <p role="status" className="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">{notice}</p>}

      <form className="mt-6 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-2" onSubmit={(event) => void handleSubmit(event)}>
        <h2 className="text-lg font-semibold md:col-span-2">{editingId ? "Edit category" : "Create category"}</h2>
        <label className="text-sm font-medium text-slate-700">
          Category name <span className="text-red-600">*</span>
          <input required maxLength={100} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.name} onChange={(event) => setValues((current) => ({ ...current, name: event.target.value }))} />
        </label>
        <div className="flex items-center gap-3 pt-6">
          <input id="requires-calibration" type="checkbox" checked={values.requires_calibration} onChange={(event) => setValues((current) => ({ ...current, requires_calibration: event.target.checked }))} />
          <label htmlFor="requires-calibration" className="text-sm text-slate-700">This category requires calibration</label>
        </div>
        <label className="text-sm font-medium text-slate-700">
          Default calibration interval (days)
          <input type="number" min={0} step={1} disabled={!values.requires_calibration} className="mt-1 w-full rounded border border-slate-300 px-3 py-2 disabled:bg-slate-100" value={values.default_calibration_interval_days} onChange={(event) => setValues((current) => ({ ...current, default_calibration_interval_days: Number(event.target.value) }))} />
        </label>
        <div className="flex items-end gap-2">
          <button disabled={saving} className="rounded bg-university-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50" type="submit">
            {saving ? "Saving…" : editingId ? "Save category" : "Create category"}
          </button>
          {editingId && (
            <button type="button" className="rounded border border-slate-300 px-4 py-2 text-sm" onClick={() => {
              setEditingId(null);
              setValues(EMPTY);
            }}>
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <form className="mt-6 flex gap-2" onSubmit={(event) => {
        event.preventDefault();
        setPage(1);
        setSearch(searchInput.trim());
      }}>
        <input aria-label="Search categories" className="w-full max-w-sm rounded border border-slate-300 px-3 py-2" placeholder="Search category names" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} />
        <button className="rounded border border-slate-300 px-4 py-2 text-sm" type="submit">Search</button>
      </form>

      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Calibration</th>
              <th className="px-4 py-3 font-medium">Default interval</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr><td className="px-4 py-6 text-slate-500" colSpan={4}>Loading categories…</td></tr>
            ) : result.items.length === 0 ? (
              <tr><td className="px-4 py-6 text-slate-500" colSpan={4}>No categories found.</td></tr>
            ) : result.items.map((category) => (
              <tr key={category.id}>
                <td className="px-4 py-3 font-medium">{category.name}</td>
                <td className="px-4 py-3">{category.requires_calibration ? "Required" : "Not required"}</td>
                <td className="px-4 py-3">{category.requires_calibration ? `${category.default_calibration_interval_days} days` : "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-3">
                    <button className="text-university-700 hover:underline" type="button" onClick={() => beginEdit(category)}>Edit</button>
                    <button className="text-red-700 hover:underline" type="button" onClick={() => void handleDelete(category)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
        <span>{result.total} categor{result.total === 1 ? "y" : "ies"}</span>
        <div className="flex items-center gap-3">
          <button className="rounded border border-slate-300 px-3 py-1.5 disabled:opacity-40" disabled={page <= 1 || loading} onClick={() => setPage((current) => current - 1)} type="button">Previous</button>
          <span>Page {result.page} of {Math.max(result.pages, 1)}</span>
          <button className="rounded border border-slate-300 px-3 py-1.5 disabled:opacity-40" disabled={page >= result.pages || loading} onClick={() => setPage((current) => current + 1)} type="button">Next</button>
        </div>
      </div>
    </section>
  );
}
