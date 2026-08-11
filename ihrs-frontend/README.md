# IHRS Frontend (v2)

## Setup

```bash
npm install
npm run dev
```

Runs at http://localhost:5173. Backend expected at http://localhost:8000/api
(`src/api/axios.js` -- change `BASE_URL` if different).

## Bugs fixed from the previous version

1. **Auth header was `Bearer <token>`, backend expects `Token <token>`.**
   This alone caused every authenticated request to fail regardless of
   how correct the rest of the code was. Fixed in `src/api/axios.js`.
2. **Login never redirected anywhere** -- it just logged to console.
   Fixed: now redirects to `/change-password` if the account has a
   temporary password, otherwise to the correct dashboard for the role.
3. **Register had a role dropdown** (doctor/nurse/patient/hospital_admin/hospital ID field).
   Removed entirely -- registration is patient-only, matching the backend,
   which forces `role: "patient"` regardless of what's sent.
4. **Any logged-in role could open the audit page**, including doctors.
   Fixed: `/audit`, `/staff/create`, and `/emergency-review` are now
   role-gated to `hospital_admin` only via `ProtectedRoute`'s `allowedRoles`.
   A doctor/nurse hitting these routes is redirected to `/not-authorized`.
5. **Dashboards were placeholders with broken logic.** Replaced with three
   role-specific dashboards (patient / clinical / admin) that actually
   call the real endpoints.

## Routes

| Path | Who | What |
|---|---|---|
| `/` | anyone | Landing page |
| `/register` | anyone | Patient registration |
| `/login` | anyone | Login |
| `/change-password` | any logged-in user | Forced for temp-password accounts |
| `/dashboard/patient` | patient | Own records + own audit trail |
| `/consent` | patient | Grant/revoke hospital consent |
| `/dashboard/clinical` | doctor, nurse | NHID search, emergency access request |
| `/records/create` | doctor, nurse | Create a record |
| `/dashboard/admin` | hospital_admin | Hub linking to the three admin tools |
| `/staff/create` | hospital_admin | Create doctor/nurse accounts |
| `/emergency-review` | hospital_admin | Review break-glass requests |
| `/audit` | hospital_admin | Load logs + verify chain integrity |

## ⚠️ Please confirm these before the defense

These were built on assumptions because the underlying view code wasn't
available -- test each one; if it 400s/404s, the fix is almost always a
field-name or URL mismatch, not a rewrite:

1. **`POST /api/consent/grant/` and `/api/consent/revoke/`** -- assumed
   body `{ "hospital": <id> }`. Paste `access_control/urls.py` and the
   grant/revoke views if this doesn't match, and I'll fix the two calls
   in `src/pages/ConsentManager.jsx`.
2. **No endpoint exists yet to list hospitals** (name -> ID), so the
   Consent Manager asks the patient to type a raw hospital ID. Worth
   adding a `GET /api/hospitals/` endpoint before the defense if there's
   time -- it's a five-minute addition and looks much better live.
3. **Login/register response has no NHID for existing patients** -- only
   registration returns one. `PatientDashboard` caches it in
   `localStorage` at signup, but a patient logging in on a different
   device (or after clearing storage) has no way to look up their own
   NHID from the frontend alone. There's a manual "enter your NHID"
   fallback for the demo, but the real fix is adding
   `patient_profile.nhid` to `UserSerializer`'s output for patient users.
4. **Emergency access URLs assumed under `/api/consent/emergency/...`**
   based on `access_control/urls.py` being included at that prefix --
   confirm this still matches after any recent changes.

## Not built yet

- Hospital lookup/directory
- Editing an existing record
- Notifications when consent is granted/revoked
