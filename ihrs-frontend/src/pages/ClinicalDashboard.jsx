import { useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import PatientInfoCard from "../components/PatientInfoCard.jsx";
import RecordCard from "../components/RecordCard.jsx";
import LifestyleSummary from "../components/LifestyleSummary.jsx";
import api from "../api/axios.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function ClinicalDashboard() {
  const { user } = useAuth();
  const [nhid, setNhid] = useState("");
  const [patient, setPatient] = useState(null);
  const [records, setRecords] = useState(null);
  const [lifestyleSummary, setLifestyleSummary] = useState(null);
  const [peersRequiringConsent, setPeersRequiringConsent] = useState([]);
  const [error, setError] = useState("");
  const [errorCode, setErrorCode] = useState("");
  const [loading, setLoading] = useState(false);

  const [justification, setJustification] = useState("");
  const [emergencySubmitting, setEmergencySubmitting] = useState(false);
  const [emergencyMessage, setEmergencyMessage] = useState("");

  async function handleSearch(e) {
    e.preventDefault();
    setError(""); setErrorCode(""); setPatient(null); setRecords(null);
    setLifestyleSummary(null); setPeersRequiringConsent([]); setEmergencyMessage("");
    setLoading(true);
    try {
      const res = await api.get(`/records/${nhid}/`);
      setPatient(res.data.data.patient);
      setRecords(res.data.data.records);
      setLifestyleSummary(res.data.data.lifestyle_summary);
      // A cross-hospital peer withholding data isn't an error at all --
      // it's a normal 200 response, just naming which OTHER hospitals
      // have more but need consent first. Distinct from errorCode,
      // which only covers THIS hospital's own local consent gate.
      setPeersRequiringConsent(res.data.data.peers_requiring_consent || []);
    } catch (err) {
      setError(err.response?.data?.message || "Could not load records.");
      setErrorCode(err.response?.data?.code || "");
    } finally {
      setLoading(false);
    }
  }

  async function handleEmergencyRequest(e) {
    e.preventDefault();
    setEmergencySubmitting(true);
    setEmergencyMessage("");
    try {
      await api.post(`/consent/emergency/request/${nhid}/`, { justification });
      setEmergencyMessage("Emergency access granted for 1 hour. Loading patient record...");
      // This follow-up GET automatically broadcasts in "emergency" mode
      // to every peer too, since read_record_view detects the
      // EmergencyAccessRequest we just created and reuses its
      // justification -- no separate cross-hospital step needed here.
      const res = await api.get(`/records/${nhid}/`);
      setPatient(res.data.data.patient);
      setRecords(res.data.data.records);
      setLifestyleSummary(res.data.data.lifestyle_summary);
      setPeersRequiringConsent(res.data.data.peers_requiring_consent || []);
      setError(""); setErrorCode("");
    } catch (err) {
      setEmergencyMessage(err.response?.data?.message || "Could not request emergency access.");
    } finally {
      setEmergencySubmitting(false);
    }
  }

  const showEmergencyOption = errorCode === "CONSENT_REQUIRED" || peersRequiringConsent.length > 0;

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Clinical dashboard</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">
          Welcome, {user?.role === "doctor" ? "Dr. " : ""}{user?.full_name?.split(" ")[0]}
        </h1>

        {user?.role === "doctor" && (
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/records/create" className="btn-secondary">Create a record</Link>
          </div>
        )}

        <form onSubmit={handleSearch} className="card mt-8 flex gap-3">
          <input
            required value={nhid} onChange={(e) => setNhid(e.target.value)}
            className="input mt-0" placeholder="Search by NHID -- NH-00001-KTM"
          />
          <button className="btn-primary shrink-0" disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        {error && (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-5">
            <p className="text-sm font-medium text-red-700">{error}</p>
          </div>
        )}

        {peersRequiringConsent.length > 0 && (
          <div className="mt-4 rounded-xl border border-sky-200 bg-sky-50 p-5">
            <p className="text-sm font-medium text-sky-700">
              {peersRequiringConsent.join(", ")} {peersRequiringConsent.length === 1 ? "has" : "have"} additional records for this patient, but consent hasn't been granted to this hospital yet.
            </p>
          </div>
        )}

        {showEmergencyOption && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-5">
            <p className="text-sm text-ink/70">
              If this is a genuine emergency, you can request break-glass
              access -- it's logged (including for any other hospital's
              records above) and reviewed by your hospital admin afterward.
            </p>
            <form onSubmit={handleEmergencyRequest} className="mt-3 space-y-2">
              <textarea
                required minLength={20} value={justification}
                onChange={(e) => setJustification(e.target.value)}
                className="input" rows={3}
                placeholder="Why do you need emergency access? (min. 20 characters)"
              />
              <button className="btn-primary" disabled={emergencySubmitting}>
                {emergencySubmitting ? "Requesting..." : "Request emergency access"}
              </button>
            </form>
            {emergencyMessage && <p className="mt-2 text-sm text-ink/60">{emergencyMessage}</p>}
          </div>
        )}

        {/* Patient demographics -- shown immediately, decrypted or not,
            since this is exactly what's needed in an emergency: blood
            group and DOB, before reading a single past visit record. */}
        {patient && <div className="mt-8"><PatientInfoCard patient={patient} /></div>}

        {records && (
          <section className="mt-6 space-y-3">
            {records.length === 0 && <div className="card text-center text-sm text-ink/50">No past visit records for this patient yet.</div>}
            {/* FIX: record_id is only unique WITHIN one hospital's own
                database (auto-increment per DB). A local record and a
                peer-hospital record can share the same record_id, which
                made React reuse the same RecordCard instance -- and its
                internal labReports state -- for two different records.
                Scoping the key by hospital name too makes it unique
                across the whole merged (local + peer) records list. */}
            {records.map((r) => <RecordCard key={`${r.hospital}-${r.record_id}`} record={r} />)}
          </section>
        )}

        <LifestyleSummary data={lifestyleSummary} />
      </main>
      <Footer />
    </div>
  );
}