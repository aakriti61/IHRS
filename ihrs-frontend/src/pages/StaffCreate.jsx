import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import api from "../api/axios.js";

export default function StaffCreate() {
  const [phone, setPhone] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("doctor");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null); setSubmitting(true);
    try {
      const res = await api.post("/auth/staff/create/", { phone, full_name: fullName, role });
      setResult(res.data.data);
      setPhone(""); setFullName("");
    } catch (err) {
      setError(err.response?.data?.message || "Could not create this account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-md flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Staff accounts</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Add hospital staff</h1>
        <p className="mt-2 text-sm text-ink/60">
          They'll receive a one-time password and must set their own on first login.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Full name</span>
            <input required value={fullName} onChange={(e) => setFullName(e.target.value)} className="input" placeholder="Dr Rajesh Shah" />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Phone number</span>
            <input required value={phone} onChange={(e) => setPhone(e.target.value)} className="input" placeholder="98XXXXXXXX" />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Role</span>
            <select value={role} onChange={(e) => setRole(e.target.value)} className="input">
              <option value="doctor">Doctor</option>
              <option value="nurse">Nurse</option>
              <option value="receptionist">Receptionist</option>
            </select>
          </label>

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? "Creating..." : "Create account"}
          </button>
        </form>

        {result && (
          <div className="card mt-6 border-gold/40 bg-gold-light/40">
            <p className="text-sm font-medium text-ink">{result.user.full_name}'s account is ready.</p>
            <p className="mt-2 text-xs text-ink/60">Share this temporary password with them directly (call, in person) -- it won't be shown again:</p>
            <p className="mt-2 select-all rounded-lg bg-white px-3 py-2 font-mono text-sm text-ink">
              {result.temporary_password}
            </p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}