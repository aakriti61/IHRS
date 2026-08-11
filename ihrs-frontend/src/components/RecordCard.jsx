import { useState } from "react";
import api from "../api/axios.js";
import { useAuth } from "../context/AuthContext.jsx";

function labelize(key) {
  return key.charAt(0).toUpperCase() + key.slice(1).replaceAll("_", " ");
}

// Must match records/serializers.py AddLabReportSerializer.LAB_TEST_CHOICES
// exactly -- the value sent here is what the backend validates against.
const LAB_TEST_TYPES = [
  ["glucose_fasting", "Fasting Blood Glucose"],
  ["hba1c", "HbA1c"],
  ["creatinine", "Serum Creatinine"],
  ["hemoglobin", "Hemoglobin"],
  ["systolic_bp", "Systolic Blood Pressure"],
  ["ldl_cholesterol", "LDL Cholesterol"],
  ["bmi", "Body Mass Index"],
];

const RISK_STYLE = {
  high: "border-red-200 bg-red-50 text-red-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-teal-light bg-teal-light text-teal-dark",
};

const CONSCIOUSNESS_LABEL = { A: "Alert", C: "New confusion", V: "Voice", P: "Pain", U: "Unresponsive" };

export default function RecordCard({ record }) {
  const { user } = useAuth();
  // is_peer_record is set ONLY on records fetched from another
  // hospital's server via broadcast (see peer_client.py). This is the
  // ONLY safe way to know "this record doesn't live in the currently
  // active hospital's own database" -- comparing hospital_id or even
  // hospital name is NOT safe here, since each hospital's database
  // has its own separate auto-increment IDs (Bir's hospital #1 and
  // TUTH's hospital #1 are unrelated rows that happen to share a
  // number) and record_id is similarly meaningless across databases.
  const canAddLabReport =
    (user?.role === "doctor" || user?.role === "nurse") && !record.is_peer_record;

  // vitals and confidential_notes get their own dedicated blocks below,
  // so they're excluded here from the generic key-value list.
  const entries = Object.entries(record.data || {})
    .filter(([k, v]) => v && k !== "vitals" && k !== "confidential_notes");

  const vitals = record.data?.vitals || {};
  const hasVitals = Object.entries(vitals).some(
    ([k, v]) => k !== "on_oxygen" && v !== null && v !== undefined && v !== ""
  );

  // Only ever present in the API response for a doctor/nurse viewer --
  // read_record_view structurally omits confidential_notes and
  // risk_score for a patient, so no extra client-side role check is
  // needed here, just a presence check.
  const confidentialNotes = record.data?.confidential_notes;

  const [labReports, setLabReports] = useState(record.lab_reports || []);
  const [showForm, setShowForm] = useState(false);

  const [testType, setTestType] = useState(LAB_TEST_TYPES[0][0]);
  const [value, setValue] = useState("");
  const [remarks, setRemarks] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleAddLabReport(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const res = await api.post(`/records/${record.record_id}/lab-report/`, {
        test_type: testType,
        value: Number(value),
        remarks,
      });
      setLabReports((prev) => [
        ...prev,
        {
          id: res.data.data.lab_report_id,
          added_by: user.full_name,
          created_at: res.data.data.created_at,
          test_type: res.data.data.test_type,
          value: res.data.data.value,
          unit: res.data.data.unit,
          remarks,
        },
      ]);
      setValue(""); setRemarks(""); setShowForm(false);
    } catch (err) {
      setError(err.response?.data?.message || "Could not add lab report.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="rounded-full bg-teal-light px-2.5 py-0.5 text-xs font-medium capitalize text-teal-dark">
          {record.visit_type}
        </span>
        {record.is_peer_record && (
          <span className="rounded-full bg-sky-50 px-2.5 py-0.5 text-xs font-medium text-sky-700">
            Fetched from {record.hospital}
          </span>
        )}
        <span className="text-xs text-ink/50">
          {new Date(record.created_at).toLocaleDateString()} -- {record.hospital} -- Dr. {record.doctor}
        </span>
      </div>

      {record.risk_score && (
        <div className={`mt-3 rounded-lg border px-3 py-2 text-sm ${RISK_STYLE[record.risk_score.risk_level] || RISK_STYLE.low}`}>
          <div className="flex items-center justify-between">
            <span className="font-medium">NEWS2 risk score: {record.risk_score.total_score}</span>
            <span className="text-xs font-semibold uppercase tracking-wide">{record.risk_score.risk_level}</span>
          </div>
        </div>
      )}

      <dl className="mt-4 space-y-2">
        {entries.length === 0 && <p className="text-sm text-ink/40">No additional details recorded.</p>}
        {entries.map(([key, val]) => (
          <div key={key} className="flex gap-3 text-sm">
            <dt className="w-28 shrink-0 text-ink/45">{labelize(key)}</dt>
            <dd className="text-ink/80">{val}</dd>
          </div>
        ))}
      </dl>

      {hasVitals && (
        <div className="mt-3 rounded-lg bg-surface p-3 text-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-ink/40">Vitals</p>
          <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-ink/70">
            {vitals.respiratory_rate != null && <span>RR: {vitals.respiratory_rate}/min</span>}
            {vitals.spo2 != null && <span>SpO2: {vitals.spo2}%{vitals.on_oxygen ? " (on O2)" : ""}</span>}
            {vitals.systolic_bp != null && <span>Systolic BP: {vitals.systolic_bp} mmHg</span>}
            {vitals.pulse != null && <span>Pulse: {vitals.pulse} bpm</span>}
            {vitals.temperature != null && <span>Temp: {vitals.temperature}&deg;C</span>}
            {vitals.consciousness && <span>Consciousness: {CONSCIOUSNESS_LABEL[vitals.consciousness]}</span>}
          </div>
        </div>
      )}

      {confidentialNotes && (
        <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-amber-700">Confidential (medico-only)</p>
          <p className="mt-1 text-ink/80">{confidentialNotes}</p>
        </div>
      )}

      {labReports.length > 0 && (
        <div className="mt-4 space-y-2 border-t border-ink/10 pt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-ink/40">Lab reports</p>
          {labReports.map((lab) => (
            // FIX: lab.id is only unique WITHIN one hospital's own
            // database, same issue as record_id above. A local lab
            // report and a peer-hospital lab report could share the
            // same numeric id, causing React to mix up state between
            // list items. Scoping the key by this record's hospital
            // makes it safe.
            <div key={`${record.hospital}-${lab.id}`} className="rounded-lg bg-surface p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink">
                  {LAB_TEST_TYPES.find(([t]) => t === lab.test_type)?.[1] || labelize(lab.test_type || "")}
                </span>
                <span className="text-xs text-ink/40">
                  {new Date(lab.created_at).toLocaleDateString()} -- {lab.added_by}
                </span>
              </div>
              <p className="mt-1 text-ink/70">{lab.value} {lab.unit}</p>
              {lab.remarks && <p className="mt-1 text-xs italic text-ink/50">{lab.remarks}</p>}
            </div>
          ))}
        </div>
      )}

      {canAddLabReport && (
        <div className="mt-4 border-t border-ink/10 pt-4">
          {!showForm ? (
            <button onClick={() => setShowForm(true)} className="text-sm font-medium text-teal-dark hover:underline">
              + Add lab report
            </button>
          ) : (
            <form onSubmit={handleAddLabReport} className="space-y-3">
              {error && <p className="text-sm text-danger">{error}</p>}

              <select value={testType} onChange={(e) => setTestType(e.target.value)} className="input mt-0">
                {LAB_TEST_TYPES.map(([t, label]) => <option key={t} value={t}>{label}</option>)}
              </select>

              <input
                required type="number" step="any" value={value} onChange={(e) => setValue(e.target.value)}
                className="input" placeholder="Numeric value"
              />
              <textarea
                value={remarks} onChange={(e) => setRemarks(e.target.value)}
                className="input" rows={1} placeholder="Remarks (optional)"
              />

              <div className="flex gap-2">
                <button type="submit" disabled={submitting} className="btn-primary px-4 py-1.5 text-xs">
                  {submitting ? "Saving..." : "Save lab report"}
                </button>
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary px-4 py-1.5 text-xs">
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
}