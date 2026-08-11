import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

const initialForm = {
  full_name: "", phone: "", email: "", dob: "",
  blood_group: "", emergency_contact: "",
};

// NOTE: this page is now RECEPTIONIST-ONLY (ticket-counter model) --
// patients no longer self-register. A logged-in receptionist fills
// this in at the front desk, and the system generates a one-time
// temporary password for the patient, shown once right here.
export default function Register() {
  const { register, loading } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setError(""); setResult(null);

    if (form.dob > new Date().toISOString().split("T")[0]) {
      setError("Date of birth cannot be in the future.");
      return;
    }

    const outcome = await register(form);
    if (outcome.success) {
      setResult(outcome);
      setForm(initialForm);
    } else {
      setError(typeof outcome.message === "string" ? outcome.message : "Please check the form and try again.");
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Reception desk</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Register a new patient</h1>
        <p className="mt-2 text-sm text-ink/60">
          Creates the patient's NHID and a one-time password. Give the
          password to the patient directly -- it's shown only once and
          they'll be asked to set their own on first login.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <Field label="Full name">
            <input required type="text" value={form.full_name} onChange={update("full_name")} className="input" placeholder="Aashish Shrestha" />
          </Field>

          <Field label="Phone number" hint="This is what the patient will log in with">
            <input required type="tel" value={form.phone} onChange={update("phone")} className="input" placeholder="98XXXXXXXX" />
          </Field>

          <Field label="Email" hint="Optional -- lets the patient log in with email too">
            <input type="email" value={form.email} onChange={update("email")} className="input" placeholder="patient@example.com" />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Date of birth">
              <input required type="date" max={new Date().toISOString().split("T")[0]} value={form.dob} onChange={update("dob")} className="input" />
            </Field>
            <Field label="Blood group">
              <select required value={form.blood_group} onChange={update("blood_group")} className="input">
                <option value="" disabled>Select</option>
                {BLOOD_GROUPS.map((bg) => <option key={bg} value={bg}>{bg}</option>)}
              </select>
            </Field>
          </div>

          <Field label="Emergency contact number">
            <input required type="tel" value={form.emergency_contact} onChange={update("emergency_contact")} className="input" placeholder="98XXXXXXXX" />
          </Field>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Registering..." : "Register patient"}
          </button>
        </form>

        {result && (
          <div className="card mt-6 border-gold/40 bg-gold-light/40">
            <p className="text-sm font-medium text-ink">{result.patientName}'s account is ready.</p>
            <p className="mt-2 text-xs text-ink/60">NHID (give this to the patient, they'll need it):</p>
            <p className="mt-1 select-all rounded-lg bg-white px-3 py-2 font-mono text-sm text-ink">
              {result.nhid}
            </p>
            <p className="mt-3 text-xs text-ink/60">Temporary password -- shown once, share it directly with the patient now:</p>
            <p className="mt-1 select-all rounded-lg bg-white px-3 py-2 font-mono text-sm text-ink">
              {result.temporaryPassword}
            </p>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink/80">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink/45">{hint}</span>}
    </label>
  );
}