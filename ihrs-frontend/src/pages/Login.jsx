import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import { useAuth, dashboardPathFor } from "../context/AuthContext.jsx";
import PasswordField from "../components/PasswordField.jsx";
export default function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const result = await login(identifier, password);
    if (!result.success) {
      setError(typeof result.message === "string" ? result.message : "Login failed. Please check your details.");
      return;
    }

    // This is the redirect that was missing entirely before -- login
    // succeeding used to just sit on the login page with no navigation.
    if (result.mustChangePassword) {
      navigate("/profile");
    } else {
      navigate(dashboardPathFor(result.role));
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Welcome back</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Log in to IHRS</h1>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

          <label className="block">
            <span className="text-sm font-medium text-ink/80">Phone or email</span>
            <input required type="text" value={identifier} onChange={(e) => setIdentifier(e.target.value)} className="input" placeholder="98XXXXXXXX or you@example.com" autoFocus />
          </label>

          <PasswordField
            label="Password" required
            value={password} onChange={(e) => setPassword(e.target.value)}
          />

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Logging in..." : "Log in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-ink/60">
          Don't have an NHID yet? Visit any partner hospital's reception desk to register.
        </p>
      </main>
      <Footer />
    </div>
  );
}