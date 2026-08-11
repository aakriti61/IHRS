import { Link, useNavigate } from "react-router-dom";
import { useAuth, dashboardPathFor } from "../context/AuthContext.jsx";
import { HOSPITAL_SERVERS, getActiveHospitalServer, setHospitalServer } from "../api/axios.js";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const activeServer = getActiveHospitalServer();

  function handleLogoClick(e) {
    e.preventDefault();
    navigate(user ? dashboardPathFor(user.role) : "/");
  }

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  function handleServerSwitch(key) {
    if (key === activeServer) return;
    setHospitalServer(key);
    // Identity just changed servers entirely -- a full reload is the
    // simplest way to guarantee no stale component state (old user,
    // old records) lingers from the previous hospital's session.
    window.location.href = "/login";
  }

  return (
    <header className="sticky top-0 z-50 border-b border-ink/10 bg-surface/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <a href="/" onClick={handleLogoClick} className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-teal font-display text-sm font-semibold text-white">
            IH
          </span>
          <span className="font-display text-lg font-medium tracking-tight text-ink">
            IHRS
          </span>
        </a>

        <div className="flex items-center gap-4">
          {/* Dev/testing aid -- picks which hospital's backend this tab
              talks to. Not something a real deployed hospital's own
              staff would ever see/need (they'd only ever use their own
              hospital's URL), but essential while running Bir and TUTH
              side by side locally for testing and the viva demo. */}
          <div className="flex items-center rounded-full border border-ink/10 bg-white p-0.5 text-xs">
            {Object.entries(HOSPITAL_SERVERS).map(([key, { label }]) => (
              <button
                key={key}
                onClick={() => handleServerSwitch(key)}
                className={`rounded-full px-3 py-1 font-medium transition ${
                  activeServer === key ? "bg-teal text-white" : "text-ink/50 hover:text-ink"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {user ? (
            <div className="flex items-center gap-4">
              <span className="hidden text-sm text-ink/70 sm:inline">
                {user.full_name}
                <span className="ml-2 rounded-full bg-teal-light px-2 py-0.5 text-xs font-medium capitalize text-teal-dark">
                  {user.role.replace("_", " ")}
                </span>
                {user.role === "patient" && (
                  <span className="ml-2 rounded-full bg-gold-light px-2 py-0.5 font-mono text-xs font-medium text-ink/70">
                    {user.nhid || localStorage.getItem("ihrs_nhid") || "NHID unavailable"}
                  </span>
                )}
              </span>
              <Link to="/profile" className="text-sm font-medium text-ink/60 transition hover:text-ink">
                   Edit profile
              </Link>
              <button onClick={handleLogout} className="btn-secondary px-4 py-1.5">
                Log out
              </button>
            </div>
          ) : (
            <Link to="/login" className="text-sm font-medium text-ink/80 transition hover:text-ink">
              Log in
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}