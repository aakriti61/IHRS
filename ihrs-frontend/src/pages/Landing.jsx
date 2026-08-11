import { useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";

const PROBLEMS = [
  { title: "Misdiagnosis", body: "Without past history, a new doctor is guessing blind -- allergies and prior diagnoses stay locked in the last hospital's filing room." },
  { title: "Duplicate tests", body: "The same blood panel, paid for twice, because Hospital B has no way to see what Hospital A already ran last month." },
  { title: "Emergency delays", body: "In the minutes that matter most, a doctor treating an unconscious patient has no record of medications or blood group to work from." },
];

const ROLE_GUIDES = {
  patient: {
    label: "Patient",
    steps: [
      "Register once to receive your NHID -- one identity, valid at every hospital on the network.",
      "When a hospital asks to treat you, grant them consent from your dashboard.",
      "Revoke that consent any time -- access ends immediately, no calls or paperwork needed.",
      "Review your audit trail to see exactly who has looked at your record, and when.",
    ],
  },
  clinical: {
    label: "Doctor & Nurse",
    steps: [
      "Look up a patient by their NHID from your dashboard.",
      "If they've granted your hospital consent, their record decrypts and opens directly.",
      "No consent on file? File an emergency access request with a justification -- for genuine urgent cases.",
      "Every record you create or view is chained into that patient's permanent audit trail.",
    ],
  },
  admin: {
    label: "Hospital Admin",
    steps: [
      "Create doctor and nurse accounts for your hospital -- staff never self-register.",
      "Each new account gets a one-time temporary password, which they must replace on first login.",
      "Review emergency access requests filed by your clinical staff after the fact.",
      "Verify any patient's audit chain on demand to confirm no entry has been tampered with.",
    ],
  },
};

export default function Landing() {
  const [activeRole, setActiveRole] = useState("patient");

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />

      {/* Hero */}
      <section className="mx-auto grid max-w-6xl gap-12 px-6 py-16 sm:py-24 lg:grid-cols-2 lg:items-center">
        <div>
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">
            National Health ID system for Nepal
          </p>
          <h1 className="font-display text-4xl font-medium leading-tight text-ink sm:text-5xl">
            Your health record follows <em className="not-italic text-teal-dark">you</em> -- not the hospital.
          </h1>
          <p className="mt-6 max-w-lg text-base leading-relaxed text-ink/70">
            When a patient treated at TUTH later walks into Bir Hospital, doctors
            today start from zero. IHRS gives every patient one National Health ID,
            so their history moves with them -- encrypted, consent-gated, and fully
            auditable.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link to="/login" className="btn-primary">Log in</Link>
            <a href="#how-it-works" className="btn-secondary">Learn more</a>
          </div>
          <p className="mt-4 text-sm text-ink/50">
            New patients are registered in person at any partner hospital's reception desk.
          </p>
        </div>

        {/* Signature element: the NHID card itself */}
        <div className="flex justify-center">
          <svg viewBox="0 0 380 240" width="100%" className="max-w-sm drop-shadow-xl" role="img" aria-label="Sample National Health ID card">
            <rect x="4" y="4" width="372" height="232" rx="20" fill="#16324F" />
            <rect x="4" y="4" width="372" height="232" rx="20" fill="none" stroke="#0E2038" strokeWidth="1" />
            <text x="32" y="44" fill="#F5E4C3" fontSize="11" letterSpacing="2" fontFamily="Inter, sans-serif" fontWeight="600">
              IHRS · NATIONAL HEALTH ID
            </text>
            <rect x="32" y="64" width="40" height="30" rx="5" fill="#C98A2C" />
            <rect x="38" y="70" width="28" height="4" fill="#16324F" opacity="0.5" />
            <rect x="38" y="78" width="28" height="4" fill="#16324F" opacity="0.5" />
            <rect x="38" y="86" width="16" height="4" fill="#16324F" opacity="0.5" />

            <text x="32" y="140" fill="white" fontSize="20" fontFamily="Fraunces, serif" fontWeight="500">
              Sita Gurung
            </text>
            <text x="32" y="163" fill="#9FB6C6" fontSize="11" fontFamily="Inter, sans-serif">
              Blood group O+ &nbsp;·&nbsp; DOB 14 May 1998
            </text>

            <text x="32" y="205" fill="#F5E4C3" fontSize="17" fontFamily="IBM Plex Mono, monospace" letterSpacing="1">
              NH-00001-KTM
            </text>

            {[0,1,2,3,4,5,6].map((i) => (
              <rect key={i} x={230 + i * 10} y="192" width="4" height="20" fill="#F5E4C3" opacity={i % 2 === 0 ? 0.9 : 0.4} />
            ))}
          </svg>
        </div>
      </section>

      {/* Problem */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl font-medium text-ink sm:text-3xl">
            Isolated records cost time, money, and sometimes lives.
          </h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {PROBLEMS.map((p) => (
              <div key={p.title} className="border-t-2 border-gold pt-4">
                <h3 className="font-display text-lg font-medium text-ink">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-ink/65">{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works, by role */}
      <section id="how-it-works" className="py-20 scroll-mt-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl font-medium text-ink sm:text-3xl">
            How it works, depending on who you are
          </h2>

          <div className="mt-8 flex flex-wrap gap-2">
            {Object.entries(ROLE_GUIDES).map(([key, r]) => (
              <button
                key={key}
                onClick={() => setActiveRole(key)}
                className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                  activeRole === key ? "bg-teal text-white" : "bg-white text-ink/60 border border-ink/10 hover:text-ink"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          <ol className="mt-8 grid gap-6 sm:grid-cols-2">
            {ROLE_GUIDES[activeRole].steps.map((step, i) => (
              <li key={i} className="flex gap-4 rounded-xl bg-white p-5 shadow-card">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-light font-display text-sm font-medium text-teal-dark">
                  {i + 1}
                </span>
                <p className="text-sm leading-relaxed text-ink/75">{step}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Trust band */}
      <section className="bg-navy py-20 text-white">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-2xl font-medium sm:text-3xl">
            Built so no single party has to be trusted blindly
          </h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            <div>
              <h3 className="text-sm font-medium uppercase tracking-wide text-gold">Encrypted at rest</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/70">
                Every record is sealed before storage, and only your hospital holds the key to unlock it.
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium uppercase tracking-wide text-gold">Patient-controlled</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/70">
                No hospital reads a record without consent the patient granted, and can revoke, themselves.
              </p>
            </div>
            <div>
              <h3 className="text-sm font-medium uppercase tracking-wide text-gold">Tamper-evident</h3>
              <p className="mt-2 text-sm leading-relaxed text-white/70">
                Every access is chained into an audit log. Alter one entry, and every entry after it stops matching.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}