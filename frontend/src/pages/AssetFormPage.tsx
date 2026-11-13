import { isAxiosError } from "axios";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  createAsset,
  getAsset,
  listAllCategories,
  listLocationOptions,
  updateAsset,
  type Asset,
  type AssetCategory,
  type CollegeOption,
  type DepartmentOption,
  type LaboratoryOption,
  type RoomOption,
} from "../services/assets";

interface AssetFormValues {
  legacy_tag_number: string;
  serial_number: string;
  model_number: string;
  manufacturer_name: string;
  category_id: string;
  laboratory_id: string;
  room_id: string;
  purchase_date: string;
  commissioning_date: string;
  warranty_expiry_date: string;
}

const EMPTY_FORM: AssetFormValues = {
  legacy_tag_number: "",
  serial_number: "",
  model_number: "",
  manufacturer_name: "",
  category_id: "",
  laboratory_id: "",
  room_id: "",
  purchase_date: "",
  commissioning_date: "",
  warranty_expiry_date: "",
};

function messageFromError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join("; ");
    }
  }
  return error instanceof Error ? error.message : "The asset could not be saved.";
}

function assetToForm(asset: Asset): AssetFormValues {
  return {
    legacy_tag_number: asset.legacy_tag_number ?? "",
    serial_number: asset.serial_number,
    model_number: asset.model_number,
    manufacturer_name: asset.manufacturer_name,
    category_id: asset.category_id,
    laboratory_id: asset.laboratory_id,
    room_id: asset.room_id,
    purchase_date: asset.purchase_date ?? "",
    commissioning_date: asset.commissioning_date ?? "",
    warranty_expiry_date: asset.warranty_expiry_date ?? "",
  };
}

function formDate(value: string): string | null {
  return value || null;
}

export default function AssetFormPage() {
  const { assetId } = useParams<{ assetId: string }>();
  const editing = Boolean(assetId);
  const navigate = useNavigate();
  const [values, setValues] = useState<AssetFormValues>(EMPTY_FORM);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [colleges, setColleges] = useState<CollegeOption[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [laboratories, setLaboratories] = useState<LaboratoryOption[]>([]);
  const [rooms, setRooms] = useState<RoomOption[]>([]);
  const [collegeId, setCollegeId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let active = true;
    const assetRequest = assetId ? getAsset(assetId) : Promise.resolve(null);
    void Promise.all([assetRequest, listAllCategories(), listLocationOptions()])
      .then(([loadedAsset, loadedCategories, locations]) => {
        if (!active) return;
        setAsset(loadedAsset);
        setValues(loadedAsset ? assetToForm(loadedAsset) : EMPTY_FORM);
        setCategories(loadedCategories);
        setColleges(locations.colleges);
        setDepartments(locations.departments);
        setLaboratories(locations.laboratories);
        setRooms(locations.rooms);
        if (loadedAsset) {
          setDepartmentId(loadedAsset.department_id);
          setCollegeId(
            locations.departments.find(
              (department) => department.id === loadedAsset.department_id,
            )?.college_id ?? "",
          );
        }
      })
      .catch((cause: unknown) => {
        if (active) setError(messageFromError(cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [assetId]);

  const visibleDepartments = departments.filter(
    (department) => !collegeId || department.college_id === collegeId,
  );
  const visibleLaboratories = laboratories.filter(
    (laboratory) =>
      (!collegeId ||
        departments.some(
          (department) =>
            department.id === laboratory.department_id &&
            department.college_id === collegeId,
        )) &&
      (!departmentId || laboratory.department_id === departmentId),
  );
  const visibleRooms = useMemo(
    () => rooms.filter((room) => room.laboratory_id === values.laboratory_id),
    [rooms, values.laboratory_id],
  );

  function updateField<K extends keyof AssetFormValues>(
    key: K,
    value: AssetFormValues[K],
  ) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      if (assetId) {
        const updated = await updateAsset(assetId, {
          legacy_tag_number: values.legacy_tag_number || null,
          serial_number: values.serial_number,
          model_number: values.model_number,
          manufacturer_name: values.manufacturer_name,
          category_id: values.category_id,
          purchase_date: formDate(values.purchase_date),
          commissioning_date: formDate(values.commissioning_date),
          warranty_expiry_date: formDate(values.warranty_expiry_date),
        });
        setAsset(updated);
        setSuccess("Asset details updated.");
      } else {
        const created = await createAsset({
          legacy_tag_number: values.legacy_tag_number || null,
          serial_number: values.serial_number,
          model_number: values.model_number,
          manufacturer_name: values.manufacturer_name,
          category_id: values.category_id,
          laboratory_id: values.laboratory_id,
          room_id: values.room_id,
          purchase_date: formDate(values.purchase_date),
          commissioning_date: formDate(values.commissioning_date),
          warranty_expiry_date: formDate(values.warranty_expiry_date),
        });
        navigate(`/assets/${created.id}`, {
          replace: true,
          state: { created: true },
        });
      }
    } catch (cause: unknown) {
      setError(messageFromError(cause));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-slate-600">Loading asset form…</p>;
  }

  return (
    <section className="mx-auto max-w-3xl">
      <Link to={assetId ? `/assets/${assetId}` : "/assets"} className="text-sm text-university-700 hover:underline">
        ← Back to {assetId ? "asset" : "assets"}
      </Link>
      <h1 className="mt-4 text-3xl font-semibold text-slate-900">
        {editing ? `Edit ${asset?.asset_code ?? "asset"}` : "Register asset"}
      </h1>
      <p className="mt-2 text-slate-600">
        Enter only the approved asset register fields. Location and custody changes are handled separately.
      </p>
      {error && <p role="alert" className="mt-4 rounded bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      {success && <p role="status" className="mt-4 rounded bg-green-50 p-3 text-sm text-green-800">{success}</p>}

      <form className="mt-6 space-y-5 rounded-xl border border-slate-200 bg-white p-6" onSubmit={(event) => void handleSubmit(event)}>
        {editing && asset && (
          <div className="rounded bg-slate-50 p-3 text-sm text-slate-700">
            Asset code: <strong>{asset.asset_code}</strong> · Status: <strong>{asset.operational_status.replace(/_/g, " ")}</strong>
          </div>
        )}
        {!editing && (
          <p className="rounded bg-blue-50 p-3 text-sm text-blue-900">
            The system assigns the asset code using the approved college/department sequence and sets initial status to OPERATIONAL.
          </p>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium text-slate-700">
            Manufacturer <span className="text-red-600">*</span>
            <input required maxLength={150} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.manufacturer_name} onChange={(event) => updateField("manufacturer_name", event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Model number <span className="text-red-600">*</span>
            <input required maxLength={100} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.model_number} onChange={(event) => updateField("model_number", event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Serial number <span className="text-red-600">*</span>
            <input required maxLength={100} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.serial_number} onChange={(event) => updateField("serial_number", event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Legacy tag number
            <input maxLength={100} className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.legacy_tag_number} onChange={(event) => updateField("legacy_tag_number", event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700 sm:col-span-2">
            Asset category <span className="text-red-600">*</span>
            <select required className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.category_id} onChange={(event) => updateField("category_id", event.target.value)}>
              <option value="">Select category</option>
              {categories.map((category) => <option key={category.id} value={category.id}>{category.name}{category.requires_calibration ? " · calibration required" : ""}</option>)}
            </select>
            {categories.length === 0 && (
              <span className="mt-1 block text-xs text-amber-700">An administrator must create an asset category before registration.</span>
            )}
          </label>
        </div>

        {editing && asset ? (
          <div className="rounded bg-slate-50 p-3 text-sm text-slate-700">
            Current custodian location: {asset.college_name} / {asset.department_name} / {asset.laboratory_name} / {asset.building_name}, room {asset.room_number}
          </div>
        ) : (
          <fieldset className="space-y-4 rounded border border-slate-200 p-4">
            <legend className="px-1 text-sm font-semibold text-slate-800">Custodian location</legend>
            {colleges.length === 0 && (
              <p className="text-sm text-amber-700">Create college, department, laboratory, and room records before registering assets.</p>
            )}
            <label className="block text-sm font-medium text-slate-700">
              College <span className="text-red-600">*</span>
              <select required className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={collegeId} onChange={(event) => {
                setCollegeId(event.target.value);
                setDepartmentId("");
                updateField("laboratory_id", "");
                updateField("room_id", "");
              }}>
                <option value="">Select college</option>
                {colleges.map((college) => <option key={college.id} value={college.id}>{college.name}</option>)}
              </select>
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Department <span className="text-red-600">*</span>
              <select required className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={departmentId} onChange={(event) => {
                setDepartmentId(event.target.value);
                updateField("laboratory_id", "");
                updateField("room_id", "");
              }}>
                <option value="">Select department</option>
                {visibleDepartments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
              </select>
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Laboratory <span className="text-red-600">*</span>
              <select required className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.laboratory_id} onChange={(event) => {
                updateField("laboratory_id", event.target.value);
                updateField("room_id", "");
              }}>
                <option value="">Select laboratory</option>
                {visibleLaboratories.map((lab) => <option key={lab.id} value={lab.id}>{lab.name} · {lab.department_name}</option>)}
              </select>
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Room <span className="text-red-600">*</span>
              <select required className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.room_id} onChange={(event) => updateField("room_id", event.target.value)}>
                <option value="">Select room</option>
                {visibleRooms.map((room) => <option key={room.id} value={room.id}>{room.building_name} · {room.room_number}</option>)}
              </select>
            </label>
          </fieldset>
        )}

        <div className="grid gap-4 sm:grid-cols-3">
          <label className="text-sm font-medium text-slate-700">
            Purchase date
            <input type="date" className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.purchase_date} onChange={(event) => updateField("purchase_date", event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Commissioning date
            <input type="date" className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.commissioning_date} onChange={(event) => updateField("commissioning_date", event.target.value)} />
          </label>
          <label className="text-sm font-medium text-slate-700">
            Warranty expiry
            <input type="date" className="mt-1 w-full rounded border border-slate-300 px-3 py-2" value={values.warranty_expiry_date} onChange={(event) => updateField("warranty_expiry_date", event.target.value)} />
          </label>
        </div>

        <div className="flex justify-end gap-3 border-t border-slate-100 pt-4">
          <Link className="rounded border border-slate-300 px-4 py-2 text-sm" to={assetId ? `/assets/${assetId}` : "/assets"}>Cancel</Link>
          <button className="rounded bg-university-700 px-5 py-2 text-sm font-medium text-white disabled:opacity-50" disabled={saving || categories.length === 0} type="submit">
            {saving ? "Saving…" : editing ? "Save changes" : "Register asset"}
          </button>
        </div>
      </form>
    </section>
  );
}
