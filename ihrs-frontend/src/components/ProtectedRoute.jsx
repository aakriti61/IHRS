import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ children, allowedRoles }) {
  const { user } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // A temp-password account must resolve that before reaching anything
  // else -- mirrors the backend's own require_permission() enforcement,
  // this is just a faster UI redirect, not a substitute for it.
  // FIX: this used to call navigate("/profile") but `navigate` was never
  // defined anywhere in this file -- only the <Navigate> component was
  // imported, not the useNavigate() hook. That threw a ReferenceError
  // and crashed the app for any fresh account (must_change_password=true)
  // the moment it tried to reach any protected route other than /profile.
  if (user.must_change_password && location.pathname !== "/profile") {
    return <Navigate to="/profile" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/not-authorized" replace />;
  }

  return children;
}