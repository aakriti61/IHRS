import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import api from "../api/axios.js";

export default function ConsentManager() {
  // NOTE: hospital_name, not hospital_id -- the backend now identifies
  // consent by name (works for both a local hospital and a peer
  // hospital that has no row in this hospital's own database at all).
  const [hospitalName, setHospitalName] = useState("");
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleGrant(e) {
    e.preventDefault();
    setError(""); setStatus(null); setSubmitting(true);
    try {
      await api.post("/consent/grant/", { hospital_name: hospitalName });
      setStatus(`Consent granted to ${hospitalName}.`);
    } catch (err) {
      setError(err.response?.data?.message || "Could not grant consent.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRevoke(e) {
    e.preventDefault();
    setError(""); setStatus(null); setSubmitting(true);
    try {
      await api.post("/consent/revoke/", { hospital_name: hospitalName });
      setStatus(`Consent revoked for ${hospitalName}.`);
    } catch (err) {
      setError(err.response?.data?.message || "Could not revoke consent.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-md flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Consent</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Manage hospital access</h1>
        <p className="mt-2 text-sm text-ink/60">
          Grant a hospital access to create and view your records, or revoke it at any time.
        </p>

        <div className="card mt-8">
          {status && <p className="mb-4 rounded-lg bg-teal-light px-4 py-3 text-sm text-teal-dark">{status}</p>}
          {error && <p className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Hospital name</span>
            <input
              required type="text" value={hospitalName}
              onChange={(e) => setHospitalName(e.target.value)}
              className="input" placeholder="e.g. Bir Hospital or TUTH"
            />
            <span className="mt-1 block text-xs text-ink/45">
              Enter the exact hospital name -- your front desk can confirm this.
            </span>
          </label>

          <div className="mt-5 flex gap-3">
            <button onClick={handleGrant} disabled={submitting || !hospitalName} className="btn-primary flex-1">
              Grant consent
            </button>
            <button onClick={handleRevoke} disabled={submitting || !hospitalName} className="btn-secondary flex-1">
              Revoke consent
            </button>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}