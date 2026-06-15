# Shared Expenses App

A full-stack expense-sharing app for flatmates **Aisha, Rohan, Priya, Meera, Dev, and Sam**. It ingests the provided messy spreadsheet export (`Expenses_Export.csv`), detects data problems, applies documented policies, and shows who owes whom — with full expense-level traceability.

Built as a software engineering internship assignment: product decisions, relational data model, deliberate import handling, and explainable balance math.

---

## Live Demo

**App:** https://shared-expenses-app-6xmk.onrender.com

| | |
|---|---|
| **Login** | `demo@flatmates.app` / `demo1234` |
| **Health check** | https://shared-expenses-app-6xmk.onrender.com/api/health |

**Quick test:** Login → create group → **Import** tab → upload `Expenses_Export.csv` → check **Balances**.

> Free tier may sleep after inactivity; first load can take 30–60 seconds.

---

## Features

| Requirement | Implementation |
|-------------|----------------|
| Login | JWT email/password auth |
| Groups with changing membership | `group_memberships` with `joined_at` / `left_at` |
| Expenses (all CSV split types) | `equal`, `unequal`, `percentage`, `share` |
| Group & individual balances | Simplified debts + per-member breakdown |
| Settlements | Separate from expenses; auto-detected on import |
| CSV import | Upload `Expenses_Export.csv` as-is — no manual edits |
| Relational DB only | SQLite (local) / PostgreSQL (production) |

### Flatmate requests addressed

- **Aisha** — simplified “who pays whom, how much” on the Balances tab
- **Rohan** — click **Details** on any member to see every expense line behind their balance
- **Priya** — USD expenses converted at a configurable rate (default ₹83/USD), not 1:1
- **Sam** — members inactive on an expense date are excluded from splits
- **Meera** — duplicates/changes flagged in the import report; items requiring approval marked `pending`

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, Flask, SQLAlchemy, Flask-JWT-Extended |
| Frontend | React 18, Vite, React Router |
| Database | SQLite (dev) · PostgreSQL (prod) |
| AI tool | [Cursor](https://cursor.com) (Claude) — see [AI_USAGE.md](AI_USAGE.md) |

---

## Prerequisites

- Python 3.11+ (3.14 works locally)
- Node.js 18+
- npm

---

## Quick Start

Open a terminal in the **project root** (`Shared-Expenses-App/`).

### 1. Backend

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
PYTHONPATH=. python backend/app.py
```

API: **http://localhost:5001**  
Health check: `curl http://localhost:5001/api/health`

> Port 5001 is used because macOS often occupies 5000 (AirPlay Receiver).

### 2. Frontend (second terminal)

```bash
cd frontend
npm install
npm run dev
```

UI: **http://localhost:5173**

### 3. Login

| Field | Value |
|-------|-------|
| Email | `demo@flatmates.app` |
| Password | `demo1234` |

A demo user is auto-created on first backend startup. You can also register a new account.

---

## Usage

1. **Login** with the demo account (or register).
2. **Create a group** — e.g. `Flat 4B`.
3. Open the group → **Import** tab → upload `Expenses_Export.csv` (do not edit the file).
4. Review the **import report** — every anomaly, policy applied, and approval status.
5. **Balances** tab — see simplified debts and individual balances.
6. Click **Details** on a member — expense-by-expense breakdown (Rohan's view).
7. **Expenses** tab — expand any row to see split allocations.
8. **Members** tab — membership timeline (Meera left March, Sam joined April).

---

## Dataset & Import

The assignment CSV is at [`Expenses_Export.csv`](Expenses_Export.csv). It contains deliberate data problems (duplicates, USD amounts, settlements logged as expenses, missing payer, inactive members in splits, etc.).

**Import policies** are documented in [SCOPE.md](SCOPE.md).  
**Engineering decisions** are in [DECISIONS.md](DECISIONS.md).

### Run import from CLI (generates report)

```bash
source venv/bin/activate
PYTHONPATH=. python scripts/run_import_test.py
```

Output: `reports/import_report.json`  
Sample result: 37 expenses, 2 settlements, 3 skipped rows, 44 anomalies logged.

### Verify data in SQLite

```bash
sqlite3 database/shared_expenses.db
```

```sql
SELECT COUNT(*) FROM expenses;
SELECT anomaly_type, COUNT(*) FROM import_anomalies GROUP BY anomaly_type;
SELECT description, amount, currency, amount_inr FROM expenses WHERE currency = 'USD';
SELECT * FROM settlements;
```

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/register` | Register |
| GET | `/api/groups` | List user's groups |
| POST | `/api/groups` | Create group |
| GET | `/api/groups/:id/expenses` | List expenses |
| POST | `/api/groups/:id/expenses` | Add expense |
| GET | `/api/groups/:id/balances` | Group balance summary |
| GET | `/api/groups/:id/balances/:userId` | Member expense breakdown |
| POST | `/api/groups/:id/settlements` | Record payment |
| POST | `/api/groups/:id/import` | Upload CSV (multipart `file`) |
| GET | `/api/groups/:id/import/sessions/:id` | Import report |

All routes except `/api/auth/*` and `/api/health` require `Authorization: Bearer <token>`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///database/shared_expenses.db` | DB connection string |
| `SECRET_KEY` | dev value | Flask secret key |
| `JWT_SECRET_KEY` | dev value | JWT signing key |
| `USD_TO_INR_RATE` | `83.0` | USD → INR conversion for import |
| `PORT` | `5001` | Backend port |

---

## Production Build

```bash
# Build frontend
cd frontend && npm install && npm run build && cd ..

# Run with Gunicorn (serves API + built React app)
source venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. gunicorn backend.app:app --bind 0.0.0.0:5001
```

For PostgreSQL in production, also install `backend/requirements-prod.txt` and set `DATABASE_URL`.

---

## Deployment (Render)

Code is pushed to GitHub: **https://github.com/jasleenjk07/Shared-Expenses-App**

### Option A — One-click Blueprint (recommended)

1. Open **[Deploy to Render](https://render.com/deploy?repo=https://github.com/jasleenjk07/Shared-Expenses-App)**
2. Sign in with GitHub and authorize Render
3. Review the blueprint — it creates:
   - **Web service** (`shared-expenses-app`) — Flask + React build
   - **PostgreSQL database** (`shared-expenses-db`) — free tier
4. Click **Apply** and wait ~5–10 minutes for the first build
5. Open the service URL when status shows **Live**

### Option B — Manual setup

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect repo `jasleenjk07/Shared-Expenses-App`
3. Render reads [`render.yaml`](render.yaml) automatically

### After deployment

- Test health: `https://YOUR-APP.onrender.com/api/health`
- Login → create group → import `Expenses_Export.csv`
- Update the [Live Demo](#live-demo) URL in this README

> **Note:** Free tier services spin down after inactivity; first load may take 30–60 seconds.

---

## Project Structure

```
Shared-Expenses-App/
├── backend/
│   ├── app.py                 # Flask entry point
│   ├── models/                # SQLAlchemy models
│   ├── routes/                # API blueprints
│   └── services/              # Import engine, balances, splits
├── frontend/
│   └── src/                   # React pages & components
├── database/
│   ├── schema.sql             # Relational DDL
│   └── shared_expenses.db     # SQLite DB (created on first run)
├── scripts/
│   └── run_import_test.py     # CLI import + report generator
├── reports/
│   └── import_report.json     # Sample import output
├── Expenses_Export.csv        # Original dataset — do not edit
├── SCOPE.md                   # Anomaly log + schema
├── DECISIONS.md               # Decision log
├── AI_USAGE.md                # AI collaboration log
└── render.yaml                # Render deployment config
```

---

## Documentation (Assignment Deliverables)

| File | Contents |
|------|----------|
| [SCOPE.md](SCOPE.md) | Every CSV anomaly detected and how it was handled; DB schema |
| [DECISIONS.md](DECISIONS.md) | Significant decisions, options considered, rationale |
| [AI_USAGE.md](AI_USAGE.md) | AI tools used, key prompts, cases where AI output was corrected |
| [reports/import_report.json](reports/import_report.json) | Sample import report from the app |

---

## AI Used

**Cursor (Claude)** — primary development collaborator for architecture, CSV import engine, balance logic, React UI, and documentation. Full disclosure in [AI_USAGE.md](AI_USAGE.md).

---

## License

Built for an internship assignment. Not licensed for commercial use unless specified by the assigner.
