# Shared Expenses App

## Stack
- **Backend:** Python 3.11+, Flask, SQLAlchemy, JWT auth
- **Frontend:** React 18 + Vite
- **Database:** SQLite (local) / PostgreSQL (production)

## AI Used
Cursor (Claude) — primary development collaborator for architecture, import logic, and UI.

## Quick Start

### Backend
```bash
cd Shared-Expenses-App
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. python backend/app.py
```
API runs at http://localhost:5001

### Frontend
```bash
cd frontend
npm install
npm run dev
```
UI at http://localhost:5173

### Demo Login
- Email: `demo@flatmates.app`
- Password: `demo1234`

## Usage Flow
1. Register or login
2. Create a group (e.g. "Flat 4B")
3. Go to **Import** tab → upload `Expenses_Export.csv`
4. Review the import report (anomalies + actions taken)
5. View **Balances** for who pays whom (Aisha's request)
6. Click **Details** on any member for expense-level breakdown (Rohan's request)

## Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | SQLite file | PostgreSQL connection string for production |
| `SECRET_KEY` | dev secret | Flask secret |
| `JWT_SECRET_KEY` | dev secret | JWT signing key |
| `USD_TO_INR_RATE` | 83.0 | Exchange rate for USD expenses |

## Production Build
```bash
cd frontend && npm run build
PYTHONPATH=. gunicorn "backend.app:create_app()" --bind 0.0.0.0:5000
```

## Project Structure
```
backend/          Flask API, models, import engine
frontend/         React SPA
database/         schema.sql, seed data
Expenses_Export.csv   Original dataset (do not edit)
SCOPE.md          Anomaly log + schema
DECISIONS.md      Decision log
AI_USAGE.md       AI collaboration log
```

## Deployed App
*(Update this URL after deploying to Render/Railway)*
