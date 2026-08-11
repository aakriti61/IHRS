import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import PatientInfoCard from "../components/PatientInfoCard.jsx";
import RecordCard from "../components/RecordCard.jsx";
import LifestyleSummary from "../components/LifestyleSummary.jsx";
import api from "../api/axios.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function PatientDashboard() {
  const { user } = useAuth();
  const nhid = user?.nhid || localStorage.getItem("ihrs_nhid");

  const [patient, setPatient] = useState(null);
  const [records, setRecords] = useState(null);
  const [lifestyleSummary, setLifestyleSummary] = useState(null);
  const [auditLogs, setAuditLogs] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function loadEverything() {
    if (!nhid) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.get(`/records/${nhid}/`);
      setPatient(res.data.data.patient);
      setRecords(res.data.data.records);
      setLifestyleSummary(res.data.data.lifestyle_summary);
    } catch (err) {
      setError(err.response?.data?.message || "Could not load records.");
    } finally {
      setLoading(false);
    }

    try {
      const auditRes = await api.get(`/audit/logs/${nhid}/`);
      setAuditLogs(auditRes.data.data);
    } catch {
      // Optional section -- the rest of the dashboard still works without it
    }
  }

  useEffect(() => { loadEverything(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Patient dashboard</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">
          Welcome, {user?.full_name?.split(" ")[0]}
          {nhid && <span className="ml-3 align-middle font-mono text-base font-normal text-ink/40">{nhid}</span>}
        </h1>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/consent" className="btn-secondary">Manage hospital consent</Link>
        </div>

        {!nhid && (
          <div className="card mt-8 text-sm text-danger">
            We couldn't find your NHID. Please log out and log in again.
          </div>
        )}

        {patient && <div className="mt-8"><PatientInfoCard patient={patient} /></div>}

        <section className="mt-8">
          <h2 className="font-display text-lg font-medium text-ink">Your records</h2>
          {loading && <p className="mt-2 text-sm text-ink/50">Loading...</p>}
          {error && <p className="mt-2 text-sm text-danger">{error}</p>}
          {records && records.length === 0 && (
            <div className="card mt-3 text-center text-sm text-ink/50">No records yet.</div>
          )}
          <div className="mt-3 space-y-3">
            {records?.map((r) => <RecordCard key={r.record_id} record={r} />)}
          </div>
        </section>

        <LifestyleSummary data={lifestyleSummary} />

        {auditLogs && (
          <section className="mt-10">
            <h2 className="font-display text-lg font-medium text-ink">Who has accessed your record</h2>
            <div className="card mt-3 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink/10 text-xs uppercase tracking-wide text-ink/40">
                    <th className="py-2 pr-4">Action</th>
                    <th className="py-2 pr-4">By</th>
                    <th className="py-2 pr-4">Hospital</th>
                    <th className="py-2">When</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="border-b border-ink/5 last:border-0">
                      <td className="py-2 pr-4">{log.action.replaceAll("_", " ").toLowerCase()}</td>
                      <td className="py-2 pr-4">{log.actor}</td>
                      <td className="py-2 pr-4">{log.hospital}</td>
                      <td className="py-2 text-xs text-ink/50">{new Date(log.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
      <Footer />
    </div>
  );
}