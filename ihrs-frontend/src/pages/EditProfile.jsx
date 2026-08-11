import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import Footer from "../components/Footer.jsx";
import PasswordField from "../components/PasswordField.jsx";
import api from "../api/axios.js";
import { useAuth, dashboardPathFor } from "../context/AuthContext.jsx";

export default function EditProfile() {
  const navigate = useNavigate();
  const { user, setUser } = useAuth();
  const isForced = !!user?.must_change_password;

  // On a forced first login, show a clear notice + button BEFORE the
  // form itself -- rather than silently landing them on a form with
  // no explanation of why they're here.
  const [acknowledged, setAcknowledged] = useState(!isForced);

  const [phone, setPhone] = useState(user?.phone || "");
  const [phoneError, setPhoneError] = useState("");
  const [phoneSuccess, setPhoneSuccess] = useState("");
  const [phoneSubmitting, setPhoneSubmitting] = useState(false);

  async function handlePhoneSubmit(e) {
    e.preventDefault();
    setPhoneError(""); setPhoneSuccess("");
    setPhoneSubmitting(true);
    try {
      const res = await api.post("/auth/profile/update-phone/", { phone });
      setUser(res.data.data.user);
      setPhoneSuccess("Phone number updated.");
    } catch (err) {
      setPhoneError(err.response?.data?.message || "Could not update phone number.");
    } finally {
      setPhoneSubmitting(false);
    }
  }

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwSubmitting, setPwSubmitting] = useState(false);

  async function handlePasswordSubmit(e) {
    e.preventDefault();
    setPwError("");

    if (newPassword !== confirmPassword) {
      setPwError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setPwError("New password must be at least 8 characters.");
      return;
    }

    setPwSubmitting(true);
    try {
      await api.post("/auth/change-password/", { old_password: oldPassword, new_password: newPassword });
      setUser((u) => ({ ...u, must_change_password: false }));
      if (isForced) navigate(dashboardPathFor(user.role));
    } catch (err) {
      setPwError(err.response?.data?.message || "Could not change password.");
    } finally {
      setPwSubmitting(false);
    }
  }

  // Step 1 of the forced flow: an unmissable notice, not a silent redirect
  if (isForced && !acknowledged) {
    return (
      <div className="flex min-h-screen flex-col bg-surface">
        <Navbar />
        <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center px-6 py-16">
          <div className="card border-gold/50 bg-gold-light/40 text-center">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-gold">Action required</p>
            <h1 className="mt-3 font-display text-2xl font-medium text-ink">
              Change your password to continue
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-ink/70">
              Your hospital admin created this account with a temporary password.
              For security, you must set your own password before you can access
              records or anything else in IHRS.
            </p>
            <button onClick={() => setAcknowledged(true)} className="btn-primary mt-6 w-full">
              Change password now
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Step 2: the actual form (also the only view for a voluntary,
  // non-forced visit to this page)
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="mx-auto w-full max-w-sm flex-1 px-6 py-16">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-teal-dark">Account</p>
        <h1 className="mt-2 font-display text-3xl font-medium text-ink">Edit profile</h1>

        {!isForced && (
          <form onSubmit={handlePhoneSubmit} className="card mt-8 space-y-3">
            <h2 className="font-display text-base font-medium text-ink">Phone number</h2>
            {phoneError && <p className="text-sm text-danger">{phoneError}</p>}
            {phoneSuccess && <p className="text-sm text-teal-dark">{phoneSuccess}</p>}
            <input
              required value={phone} onChange={(e) => setPhone(e.target.value)}
              className="input mt-0" placeholder="98XXXXXXXX"
            />
            <button disabled={phoneSubmitting} className="btn-secondary w-full">
              {phoneSubmitting ? "Saving..." : "Update phone number"}
            </button>
          </form>
        )}

        <form onSubmit={handlePasswordSubmit} className="card mt-6 space-y-4">
          <h2 className="font-display text-base font-medium text-ink">
            {isForced ? "Set your own password" : "Change password"}
          </h2>
          {pwError && <p className="text-sm text-danger">{pwError}</p>}

          <PasswordField
            label="Current password" required
            value={oldPassword} onChange={(e) => setOldPassword(e.target.value)}
          />
          <PasswordField
            label="New password" required minLength={8}
            value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
            placeholder="At least 8 characters"
          />
          <PasswordField
            label="Confirm new password" required
            value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
          />

          <button type="submit" disabled={pwSubmitting} className="btn-primary w-full">
            {pwSubmitting ? "Saving..." : "Save new password"}
          </button>
        </form>
      </main>
      <Footer />
    </div>
  );
}