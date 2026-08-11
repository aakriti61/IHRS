import { Link } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import { useAuth, dashboardPathFor } from "../context/AuthContext.jsx";

export default function NotAuthorized() {
  const { user } = useAuth();
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center px-6 py-16 text-center">
        <h1 className="font-display text-2xl font-medium text-ink">This page isn't available for your role</h1>
        <p className="mt-2 text-sm text-ink/60">
          {user?.role === "doctor" || user?.role === "nurse"
            ? "Audit verification is restricted to hospital admins -- clinical staff can see the records they access, not the full trail."
            : "Your account doesn't have access to this section."}
        </p>
        <Link to={dashboardPathFor(user?.role)} className="btn-primary mt-6">Back to my dashboard</Link>
      </main>
      <Footer />
    </div>
  );
}
