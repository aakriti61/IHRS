import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import api from "../api/axios.js";

export default function AuditLog() {
  const [nhid, setNhid] = useState("");
  const [logs, setLogs] = useState(null);
  const [integrity, setIntegrity] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLoad(e) {
    e.preventDefault();
    setError(""); setIntegrity(null); setLoading(true);
    try {
      const res = await api.get(`/audit/logs/${nhid}/`);
      setLogs(res.data.data);
    } catch (err) {
      setError(err.response?.data?.message || "Could not load audit logs for this NHID.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify() {
    setError("");
    try {
      const res = await api.get(`/audit/verify/${nhid}/`);
      setIntegrity(res.data.data);
    } catch (err) {
      setError(err.response?.data?.message || "Could not verify log integrity.");
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Audit trail</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Verify a patient's record history</h1>

        <form onSubmit={handleLoad} className="card mt-8 flex flex-wrap gap-3">
          <input
            required value={nhid} onChange={(e) => setNhid(e.target.value)}
            className="input mt-0 flex-1" placeholder="NH-00001-KTM"
          />
          <button className="btn-primary" disabled={loading}>{loading ? "Loading..." : "Load logs"}</button>
          <button type="button" onClick={handleVerify} className="btn-secondary">Verify integrity</button>
        </form>

        {error && <p className="mt-4 text-sm text-danger">{error}</p>}

        {integrity && (
          <div className={`mt-6 rounded-xl p-5 ${integrity.is_valid ? "bg-teal-light" : "bg-red-50 border border-red-200"}`}>
            <p className={`font-medium ${integrity.is_valid ? "text-teal-dark" : "text-red-700"}`}>
              {integrity.is_valid ? "Chain intact -- no tampering detected." : `Tampering detected at entry #${integrity.broken_at_entry_id}.`}
            </p>
          </div>
        )}

        {logs && (
          <div className="card mt-6 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ink/10 text-xs uppercase tracking-wide text-ink/40">
                  <th className="py-2 pr-4">Actor</th>
                  <th className="py-2 pr-4">Action</th>
                  <th className="py-2 pr-4">Hospital</th>
                  <th className="py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-ink/5 last:border-0">
                    <td className="py-2 pr-4">{log.actor}</td>
                    <td className="py-2 pr-4">{log.action.replaceAll("_", " ").toLowerCase()}</td>
                    <td className="py-2 pr-4">{log.hospital}</td>
                    <td className="py-2 text-xs text-ink/50">{new Date(log.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
