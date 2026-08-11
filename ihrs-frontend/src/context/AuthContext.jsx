import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/axios.js";

const AuthContext = createContext(null);

// Single source of truth for "where does this role land after login" --
// used by Login.jsx (redirect after auth) and Navbar.jsx (logo click).
export function dashboardPathFor(role) {
  if (role === "patient") return "/dashboard/patient";
  if (role === "doctor" || role === "nurse") return "/dashboard/clinical";
  if (role === "hospital_admin") return "/dashboard/admin";
  if (role === "receptionist") return "/patients/register";
  return "/";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem("ihrs_user");
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) localStorage.setItem("ihrs_user", JSON.stringify(user));
    else localStorage.removeItem("ihrs_user");
  }, [user]);

 async function login(identifier, password) {
    setLoading(true);
    try {
      const res = await api.post("/auth/login/", { identifier, password });
      const { user: userData, token, must_change_password } = res.data.data;
      localStorage.setItem("ihrs_token", token);
      if (userData.nhid) {
        localStorage.setItem("ihrs_nhid", userData.nhid);
      }
      // Backend returns must_change_password as a SIBLING of "user", not
      // nested inside it -- attach it onto the stored user object here so
      // ProtectedRoute and EditProfile (which read user.must_change_password)
      // actually see the correct value.
      const fullUser = { ...userData, must_change_password };
      setUser(fullUser);
      return { success: true, mustChangePassword: !!must_change_password, role: userData.role };
    } catch (err) {
      return { success: false, message: err.response?.data?.message || "Login failed. Please try again." };
    } finally {
      setLoading(false);
    }
}

  async function register(formData) {
    // IMPORTANT: this is now called BY a logged-in receptionist, to
    // create a PATIENT's account -- not by the patient self-signing up.
    // It must NOT touch the receptionist's own session (no setUser,
    // no token storage) -- it just returns the created patient's NHID
    // and one-time temp password so the receptionist's screen can
    // display them to hand over to the patient.
    setLoading(true);
    try {
      const res = await api.post("/auth/register/", formData);
      return {
        success: true,
        nhid: res.data.data.nhid,
        temporaryPassword: res.data.data.temporary_password,
        patientName: res.data.data.user.full_name,
      };
    } catch (err) {
      return { success: false, message: err.response?.data?.message || "Registration failed." };
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    try {
      await api.post("/auth/logout/");
    } catch {
      // Intent to log out on this device should always succeed locally,
      // even if the server call fails (e.g. token already expired).
    }
    localStorage.removeItem("ihrs_token");
    localStorage.removeItem("ihrs_nhid");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}