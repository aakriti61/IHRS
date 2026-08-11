import { useEffect, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import api from "../api/axios.js";

export default function EmergencyReview() {
  const [pending, setPending] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      const res = await api.get("/consent/emergency/pending/");
      setPending(res.data.data);
    } catch (err) {
      setError(err.response?.data?.message || "Could not load pending requests.");
    }
  }

  useEffect(() => { load(); }, []);

  async function markReviewed(id) {
    try {
      await api.post(`/consent/emergency/review/${id}/`);
      load();
    } catch (err) {
      setError(err.response?.data?.message || "Could not mark this reviewed.");
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Break-glass log</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Emergency access requests</h1>
        <p className="mt-2 text-sm text-ink/60">
          Each request was already granted at the time it was filed. This is a
          post-hoc review, not a gate.
        </p>

        {error && <p className="mt-4 text-sm text-danger">{error}</p>}

        {pending && pending.length === 0 && (
          <div className="card mt-8 text-center text-sm text-ink/50">Nothing pending review.</div>
        )}

        <div className="mt-6 space-y-3">
          {pending?.map((req) => (
            <div key={req.id} className="card">
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink">Dr. {req.doctor} → {req.patient}</span>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${req.is_active ? "bg-teal-light text-teal-dark" : "bg-ink/5 text-ink/50"}`}>
                  {req.is_active ? "Active" : "Expired"}
                </span>
              </div>
              <p className="mt-2 text-sm italic text-ink/70">"{req.justification}"</p>
              <p className="mt-2 text-xs text-ink/45">
                Requested {new Date(req.requested_at).toLocaleString()} -- expires {new Date(req.expires_at).toLocaleString()}
              </p>
              <button onClick={() => markReviewed(req.id)} className="btn-secondary mt-3 px-4 py-1.5 text-xs">
                Mark reviewed
              </button>
            </div>
          ))}
        </div>
      </main>
      <Footer />
    </div>
  );
}
