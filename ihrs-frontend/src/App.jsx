import { Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import Register from "./pages/Register.jsx";
import Login from "./pages/Login.jsx";
import EditProfile from "./pages/EditProfile.jsx";
import PatientDashboard from "./pages/PatientDashboard.jsx";
import ClinicalDashboard from "./pages/ClinicalDashboard.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import CreateRecord from "./pages/CreateRecord.jsx";
import ConsentManager from "./pages/ConsentManager.jsx";
import StaffCreate from "./pages/StaffCreate.jsx";
import EmergencyReview from "./pages/EmergencyReview.jsx";
import AuditLog from "./pages/AuditLog.jsx";
import NotAuthorized from "./pages/NotAuthorized.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/not-authorized" element={<NotAuthorized />} />

      <Route path="/profile" element={
        <ProtectedRoute><EditProfile /></ProtectedRoute>
      } />

      {/* Patient registration moved off the public path -- it's now
          receptionist-only, ticket-counter style (see Register.jsx) */}
      <Route path="/patients/register" element={
        <ProtectedRoute allowedRoles={["receptionist"]}><Register /></ProtectedRoute>
      } />

      <Route path="/dashboard/patient" element={
        <ProtectedRoute allowedRoles={["patient"]}><PatientDashboard /></ProtectedRoute>
      } />
      <Route path="/consent" element={
        <ProtectedRoute allowedRoles={["patient"]}><ConsentManager /></ProtectedRoute>
      } />

      <Route path="/dashboard/clinical" element={
        <ProtectedRoute allowedRoles={["doctor", "nurse"]}><ClinicalDashboard /></ProtectedRoute>
      } />
      <Route path="/records/create" element={
        <ProtectedRoute allowedRoles={["doctor", "nurse"]}><CreateRecord /></ProtectedRoute>
      } />

      {/* Audit verification is hospital_admin only -- this is the fix for
          the bug where any logged-in role, including doctor, could open it */}
      <Route path="/dashboard/admin" element={
        <ProtectedRoute allowedRoles={["hospital_admin"]}><AdminDashboard /></ProtectedRoute>
      } />
      <Route path="/staff/create" element={
        <ProtectedRoute allowedRoles={["hospital_admin"]}><StaffCreate /></ProtectedRoute>
      } />
      <Route path="/emergency-review" element={
        <ProtectedRoute allowedRoles={["hospital_admin"]}><EmergencyReview /></ProtectedRoute>
      } />
      <Route path="/audit" element={
        <ProtectedRoute allowedRoles={["hospital_admin"]}><AuditLog /></ProtectedRoute>
      } />
    </Routes>
  );
}