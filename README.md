# Shared Expenses App

A full-stack expense-sharing app for flatmates **Aisha, Rohan, Priya, Meera, Dev, and Sam**. It ingests the provided spreadsheet export (`Expenses_Export.csv`), detects data problems, applies documented policies, and shows who owes whom — with full expense-level traceability.

**Live app:** https://shared-expenses-app-6xmk.onrender.com  
**Repo:** https://github.com/jasleenjk07/Shared-Expenses-App

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/jasleenjk07/Shared-Expenses-App.git
cd Shared-Expenses-App
```

### 2. Backend

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
PYTHONPATH=. python backend/app.py
```

- API runs at **http://localhost:5001**
- Verify: `curl http://localhost:5001/api/health` → `{"status":"ok"}`
- Port 5001 avoids conflict with macOS AirPlay on port 5000

### 3. Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

- UI runs at **http://localhost:5173**
- API requests are proxied to port 5001

### 4. Login and test

| Field | Value |
|-------|-------|
| Email | `demo@flatmates.app` |
| Password | `demo1234` |

Demo user is created automatically on first backend start. You can also register a new account.

### 5. Import the dataset

1. Login → **Create a group** (e.g. `Flat 4B`)
2. Open the group → **Import** tab
3. Upload `Expenses_Export.csv` from the project root (**do not edit the file**)
4. Review the import report (anomalies + actions taken)
5. Check **Balances** and **Expenses** tabs

### Optional: CLI import test

```bash
source venv/bin/activate
PYTHONPATH=. python scripts/run_import_test.py
```

Writes `reports/import_report.json` (37 expenses, 2 settlements, 44 anomalies in sample run).

### Environment variables (local defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | SQLite in `database/` | Set to PostgreSQL URL in production |
| `USD_TO_INR_RATE` | `83.0` | USD → INR rate for CSV import |
| `PORT` | `5001` | Backend port |

### Production / local build

```bash
cd frontend && npm run build && cd ..
source venv/bin/activate
PYTHONPATH=. gunicorn backend.app:app --bind 0.0.0.0:5001
```

Deployed on Render via [`render.yaml`](render.yaml) with PostgreSQL. See [Live Demo](#live-demo) for the public URL.

---

## Live Demo

| | |
|---|---|
| **App** | https://shared-expenses-app-6xmk.onrender.com |
| **Login** | `demo@flatmates.app` / `demo1234` |
| **Health** | https://shared-expenses-app-6xmk.onrender.com/api/health |

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
| CSV import | Upload `Expenses_Export.csv` as-is |
| Relational DB | SQLite (local) / PostgreSQL (production) |

---

## AI Used

**Tool:** [Cursor](https://cursor.com) with Claude (Auto agent)

AI was used as a development collaborator on **high-complexity tasks only**. Routine code (CRUD routes, basic UI, config) was written directly or with minimal assistance. Full log with prompts and corrections: [AI_USAGE.md](AI_USAGE.md).

| Task | How AI was used |
|------|-----------------|
| **CSV import engine** | Designed anomaly detection and handling policies for all 20+ data problems in `Expenses_Export.csv` (duplicates, USD conversion, settlements, inactive members, ambiguous dates) |
| **Balance calculation** | Greedy debt simplification and per-member expense breakdown for traceable balances |
| **Database schema** | Relational model for membership timelines, expense splits, settlements, and import audit trail |

**Human review:** Every import policy was verified against the raw CSV. Balance math is traceable line-by-line for the live evaluation session.

---

## Documentation

| File | Contents |
|------|----------|
| [SCOPE.md](SCOPE.md) | CSV anomaly log + database schema |
| [DECISIONS.md](DECISIONS.md) | Engineering decision log |
| [AI_USAGE.md](AI_USAGE.md) | AI prompts, mistakes caught, and fixes |
| [reports/import_report.json](reports/import_report.json) | Sample import report |

---

## Project Structure

```
backend/          Flask API, models, import engine, balance logic
frontend/         React SPA (Vite)
database/         schema.sql, SQLite DB (local)
Expenses_Export.csv   Original dataset — do not edit
scripts/          CLI import test
reports/          Sample import output
```

---

## Tech Stack

Python 3.11 · Flask · SQLAlchemy · React 18 · Vite · PostgreSQL (prod) / SQLite (dev)
