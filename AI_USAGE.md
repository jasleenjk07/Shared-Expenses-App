# AI_USAGE.md

## Tools Used
- **Cursor IDE** with Claude (Auto agent) — primary development collaborator
- Used for: architecture design, backend import engine, React UI, documentation

## Key Prompts

1. **Initial scoping:** "Build a shared expenses app from Expenses_Export.csv with login, groups, membership changes, all split types, CSV import with anomaly detection, balances, and settlements. Document every data problem."

2. **Import engine:** "Analyze Expenses_Export.csv row by row. For each deliberate data problem, write detection logic and a documented policy. No silent guesses, no crash on bad data."

3. **Balance traceability:** "Rohan wants to see exactly which expenses make up his balance. Add a per-member breakdown endpoint and UI."

## Three Cases Where AI Output Was Wrong

### Case 1: Config typo `os.environ.join`
**What AI produced:** `UPLOAD_FOLDER = os.environ.join(basedir, "..", "uploads")`  
**How caught:** Would fail at runtime — `os.environ` has no `join` method  
**Fix:** Changed to `os.path.join(...)`

### Case 2: Import path assumptions
**What AI produced:** Initial models used relative imports assuming `cd backend` execution  
**How caught:** Running `python backend/app.py` from project root failed with `ModuleNotFoundError: backend`  
**Fix:** Standardized on `PYTHONPATH=.` from project root; all imports use `backend.` prefix

### Case 3: Duplicate Thalassa dinner logic
**What AI produced:** First version only checked exact amount match for duplicates, missing the Aisha/Rohan conflict (same event, different amounts ₹2,400 vs ₹2,450)  
**How caught:** Manual CSV review — row 25 note says "Aisha also logged this"  
**Fix:** Added `DUPLICATE_CONFLICT` detection using `descriptions_similar()` without requiring same amount or payer

## Human Review
All import policies were verified against the raw CSV. Balance calculation was designed to be traceable line-by-line for the live evaluation session.
