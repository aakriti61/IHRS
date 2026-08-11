import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import { useAuth } from "../context/AuthContext.jsx";

const TILES = [
  { to: "/staff/create", title: "Add staff", body: "Create a doctor or nurse account for your hospital." },
  { to: "/emergency-review", title: "Emergency access log", body: "Review break-glass requests filed by your clinical staff." },
  { to: "/audit", title: "Verify an audit trail", body: "Check any patient's record history for tampering." },
];

export default function AdminDashboard() {
  const { user } = useAuth();
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Hospital admin</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">
          Welcome, {user?.full_name?.split(" ")[0]}
        </h1>

        <div className="mt-10 grid gap-5 sm:grid-cols-3">
          {TILES.map((t) => (
            <Link key={t.to} to={t.to} className="card transition hover:border-teal/40 hover:shadow-lg">
              <h2 className="font-display text-lg font-medium text-ink">{t.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-ink/60">{t.body}</p>
            </Link>
          ))}
        </div>
      </main>
      <Footer />
    </div>
  );
}
