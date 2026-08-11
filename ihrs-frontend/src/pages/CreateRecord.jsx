import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import api from "../api/axios.js";

export default function CreateRecord() {
  const navigate = useNavigate();
  const [nhid, setNhid] = useState("");
  const [visitType, setVisitType] = useState("routine");
  const [diagnosis, setDiagnosis] = useState("");
  const [prescription, setPrescription] = useState("");
  const [notes, setNotes] = useState("");
  const [confidentialNotes, setConfidentialNotes] = useState("");

  // Vitals -- structured numbers, not free text, so NEWS2 can actually
  // be calculated server-side. All optional: not every visit captures
  // every vital, and calculate_news2() treats a missing value as
  // contributing 0 to the score rather than failing.
  const [respiratoryRate, setRespiratoryRate] = useState("");
  const [spo2, setSpo2] = useState("");
  const [onOxygen, setOnOxygen] = useState(false);
  const [systolicBp, setSystolicBp] = useState("");
  const [pulse, setPulse] = useState("");
  const [consciousness, setConsciousness] = useState("A");
  const [temperature, setTemperature] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function toNumberOrNull(v) {
    return v === "" ? null : Number(v);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setSuccess("");
    setSubmitting(true);
    try {
      // NOTE: flat shape, matching CreateRecordSerializer -- NOT
      // wrapped under a "record_data" key anymore. The serializer's
      // own validate() assembles record_data server-side from these
      // top-level fields before encryption.
      await api.post("/records/create/", {
        patient_nhid: nhid,
        visit_type: visitType,
        diagnosis,
        prescription,
        notes,
        confidential_notes: confidentialNotes,
        vitals: {
          respiratory_rate: toNumberOrNull(respiratoryRate),
          spo2: toNumberOrNull(spo2),
          on_oxygen: onOxygen,
          systolic_bp: toNumberOrNull(systolicBp),
          pulse: toNumberOrNull(pulse),
          consciousness,
          temperature: toNumberOrNull(temperature),
        },
      });
      setSuccess("Record encrypted and saved.");
      setTimeout(() => navigate("/dashboard/clinical"), 1200);
    } catch (err) {
      setError(err.response?.data?.message || "Could not save this record.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-lg flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">New record</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Create a health record</h1>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
          {success && <div className="rounded-lg bg-teal-light px-4 py-3 text-sm text-teal-dark">{success}</div>}

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Patient NHID</span>
            <input required value={nhid} onChange={(e) => setNhid(e.target.value)} className="input" placeholder="NH-00001-KTM" />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Visit type</span>
            <select value={visitType} onChange={(e) => setVisitType(e.target.value)} className="input">
              <option value="routine">Routine</option>
              <option value="followup">Follow-up</option>
              <option value="emergency">Emergency</option>
            </select>
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Diagnosis</span>
            <input required value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} className="input" placeholder="Seasonal flu" />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Prescription</span>
            <input value={prescription} onChange={(e) => setPrescription(e.target.value)} className="input" placeholder="Paracetamol 500mg" />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">
              Notes <span className="font-normal text-ink/40">(visible to patient)</span>
            </span>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="input" rows={3} />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">
              Confidential notes <span className="font-normal text-ink/40">(medico-only -- never shown to patient)</span>
            </span>
            <textarea
              value={confidentialNotes} onChange={(e) => setConfidentialNotes(e.target.value)}
              className="input border-amber-300" rows={2}
              placeholder="e.g. suspected non-compliance, sensitive findings not yet disclosed"
            />
          </label>

          <div className="rounded-xl border border-ink/10 p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-ink/40">Vitals (for risk scoring)</p>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-xs text-ink/60">Respiratory rate (/min)</span>
                <input type="number" value={respiratoryRate} onChange={(e) => setRespiratoryRate(e.target.value)} className="input mt-1" />
              </label>
              <label className="block">
                <span className="text-xs text-ink/60">SpO2 (%)</span>
                <input type="number" value={spo2} onChange={(e) => setSpo2(e.target.value)} className="input mt-1" />
              </label>
              <label className="block">
                <span className="text-xs text-ink/60">Systolic BP (mmHg)</span>
                <input type="number" value={systolicBp} onChange={(e) => setSystolicBp(e.target.value)} className="input mt-1" />
              </label>
              <label className="block">
                <span className="text-xs text-ink/60">Pulse (bpm)</span>
                <input type="number" value={pulse} onChange={(e) => setPulse(e.target.value)} className="input mt-1" />
              </label>
              <label className="block">
                <span className="text-xs text-ink/60">Temperature (°C)</span>
                <input type="number" step="0.1" value={temperature} onChange={(e) => setTemperature(e.target.value)} className="input mt-1" />
              </label>
              <label className="block">
                <span className="text-xs text-ink/60">Consciousness (ACVPU)</span>
                <select value={consciousness} onChange={(e) => setConsciousness(e.target.value)} className="input mt-1">
                  <option value="A">Alert</option>
                  <option value="C">New confusion</option>
                  <option value="V">Voice</option>
                  <option value="P">Pain</option>
                  <option value="U">Unresponsive</option>
                </select>
              </label>
              <label className="mt-1 flex items-center gap-2">
                <input type="checkbox" checked={onOxygen} onChange={(e) => setOnOxygen(e.target.checked)} />
                <span className="text-xs text-ink/60">On supplemental oxygen</span>
              </label>
            </div>
          </div>

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Saving..." : "Save record"}
          </button>
        </form>
      </main>
      <Footer />
    </div>
  );
}