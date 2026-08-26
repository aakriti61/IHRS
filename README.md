# IHRS — Interoperable Hospital Record Sharing System

IHRS is a full-stack web application for securely managing patient health records across hospitals. It supports encrypted record storage, patient-controlled data consent, emergency access with mandatory review, and a tamper-evident audit trail — built as a final year project.

## Features

- **Authentication & roles** — registration, login/logout, password management, and staff account creation (`accounts` app)
- **Health records** — create and read patient health records and lab reports, looked up by a national health ID (NHID) (`records` app)
- **Encryption** — health data is protected using AES and RSA (`crypto` app)
- **Consent management** — patients can grant or revoke access to their records; supports emergency access requests with a pending-review workflow for oversight (`access_control` app)
- **Peer hospital sync** — consent/records can be synced across peer hospitals
- **Clinical early-warning score** — NEWS2 vitals-based deterioration score, computed for clinicians only (`records/clinical_scores.py`)
- **Lifestyle recommendations** — rule-based, guideline-referenced lifestyle guidance generated from a patient's lab trends (`records/lifestyle_engine.py`)
- **Audit logging** — every access is logged, with an endpoint to verify the integrity of the audit chain (`audit` app)
- **Admin, clinical, and patient dashboards** — separate frontend views for admins, clinicians, and patients

## Tech Stack

**Backend**
- Python 3, Django 5.2, Django REST Framework
- PostgreSQL 
- Token authentication (`rest_framework.authtoken`)
- `django-cors-headers` for CORS
- Custom AES/RSA crypto module for record encryption

**Frontend**
- React 18 + Vite
- React Router v6
- Tailwind CSS
- Axios for API calls

## Project Structure

```
ihrs-project/
├── ihrs-backend/
│   ├── ihrs/              # Django project settings & root URLs
│   ├── accounts/          # Auth, users, hospitals, staff
│   ├── records/           # Health records & lab reports
│   ├── access_control/    # Consent & emergency access
│   ├── audit/              # Audit logging & chain verification
│   ├── crypto/             # AES/RSA encryption utilities
│   ├── manage.py
│   └── requirements.txt
└── ihrs-frontend/
    ├── src/
    │   ├── api/            # Axios instance
    │   ├── components/     # Navbar, Footer, RecordCard, ProtectedRoute, etc.
    │   ├── context/        # AuthContext
    │   └── pages/           # Landing, Login, Register, Dashboards, etc.
    ├── package.json
    └── vite.config.js
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally (or accessible remotely)

### Backend setup

```bash
cd ihrs-backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `ihrs-backend/` with the following variables:

```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_django_secret_key
```

Then run migrations and start the server:

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin access
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

### Frontend setup

```bash
cd ihrs-frontend
npm install
npm run dev
```

The app will be available at `http://127.0.0.1:5173/`.

## API Overview

| Base path | App | Purpose |
|---|---|---|
| `/api/auth/` | accounts | Register, login, logout, change password, staff creation |
| `/api/records/` | records | Create/read health records, lab reports, external lookups |
| `/api/consent/` | access_control | Grant/revoke consent, emergency access requests & review, peer sync |
| `/api/audit/` | audit | View audit logs by patient, verify audit chain integrity |
| `/admin/` | Django admin | Backend admin panel |

## Algorithms

All cryptographic and integrity algorithms in this project are implemented **from scratch in pure Python** (no external crypto libraries), as this is a core part of the project's academic scope — the code lives in `ihrs-backend/crypto/`.

### AES-128 (CBC mode) — `crypto/aes.py`
- Implements the full AES-128 block cipher by hand, following the FIPS-197 standard: `SubBytes`, `ShiftRows`, `MixColumns`, `AddRoundKey`, key expansion (10 rounds), and their inverses for decryption.
- Runs in **CBC mode** with a random 16-byte IV generated per encryption (prepended to the ciphertext), and PKCS#7 padding.
- Used to encrypt the actual health record data.
- Verified against the official FIPS-197 test vector (`python crypto/aes.py`).

### RSA-512 — `crypto/rsa.py`
- Implements RSA key generation and encryption/decryption from scratch: Miller-Rabin primality testing, the Extended Euclidean Algorithm for modular inverses, and modular exponentiation.
- Each hospital has an RSA keypair. The AES key used to encrypt a health record is itself encrypted with the hospital's RSA **public** key (hybrid encryption), and only that hospital's **private** key can recover it.
- A 512-bit modulus is used deliberately for this project so the from-scratch primality testing and exponentiation stay fast enough to demo — it is **not secure at production scale** (trivially factorable on modern hardware). A real deployment would use 2048+ bit keys via a vetted library. This trade-off is documented directly in the code for the viva.

### Hybrid encryption flow
1. Generate a random one-time AES-128 key.
2. Encrypt the health record with AES-128-CBC using that key.
3. Encrypt the AES key itself with the hospital's RSA public key.
4. Store the AES-encrypted record + RSA-encrypted key together.
5. On read, the hospital's RSA private key recovers the AES key, which then decrypts the record.

### Tamper-evident audit chain — `audit` app
- Every `AuditLog` entry stores a `hash` and the `prev_hash` of the entry before it, forming a SHA-256 hash chain (blockchain-style linked hashing).
- `GET /api/audit/verify/<nhid>/` recomputes the chain and confirms each entry's hash matches, which detects whether any historical log entry has been altered or deleted out of order.

### NEWS2 — National Early Warning Score 2 — `records/clinical_scores.py`
- Implements the Royal College of Physicians' **NEWS2** early-warning score, a published, non-proprietary scoring table (not a trained model) used in NHS hospitals to flag deteriorating patients from six routine vital signs: respiratory rate, SpO₂, supplemental oxygen use, systolic blood pressure, pulse, consciousness level (ACVPU), and temperature.
- Each vital is scored 0–3 against the official RCP thresholds; the scores sum to a `total_score`.
- Risk banding follows the RCP standard: `total_score >= 7` → **high**; `total_score >= 5` **or** any single parameter scoring 3 → **medium** (one extreme reading matters clinically on its own, even if the total looks moderate); otherwise **low**.
- Computed at **read time** from decrypted vitals and never stored in plaintext. It's only attached to a record's response for clinical roles (doctor/nurse) — patients never see it.
- Chosen deliberately over a machine-learning approach: there's no real patient dataset to train on, so a fixed, citable, RCP-published lookup table keeps every scoring decision defensible in a viva.

### Lifestyle recommendation engine — `records/lifestyle_engine.py`
A rule-based (not ML-based) engine that turns a patient's lab history into plain-language lifestyle guidance, in two stages:

1. **Threshold classification** — each lab value (fasting glucose, HbA1c, systolic BP, LDL cholesterol, BMI, hemoglobin, creatinine) is classified into a band (e.g. `normal`, `prediabetes`, `hypertension_stage1`) using cutoffs taken directly from named clinical guidelines: ADA (diabetes), ACC/AHA 2017 (hypertension), NCEP ATP III (cholesterol), WHO (BMI and hemoglobin).
2. **Trend detection** — a "delta check" compares a patient's newest lab result to their own immediately preceding result (percent change), classifying it as `rising`, `falling`, `stable`, or `insufficient_data` — the same idea lab quality-control systems use, rather than only comparing against a population reference range.

The band and the trend are then combined: a value that's borderline **and** rising gets a firmer recommendation than the same borderline value that's stable, and even a normal-range value gets a light heads-up if it's trending upward. `build_lifestyle_summary()` runs this across a patient's full lab history and returns one summary per test type, surfaced to the frontend via `LifestyleSummary.jsx`.

## Security Notes

- Patient records are encrypted using AES/RSA before storage.
- All record access is written to an audit log with chain verification to detect tampering.
- Emergency access to a patient's record requires a follow-up review, rather than being granted unconditionally.
- The `.env` file (database credentials, secret key) is excluded from version control via `.gitignore` — never commit real credentials.

## Author

Final Year Project — *(Padmakanya Mutiple Campus/ Tribhuvan University)*

## License

This project is submitted as part of academic coursework and is provided for educational purposes.
