# DECISIONS.md — Decision Log

## 1. Tech Stack: Flask + React + SQLAlchemy

**Options:** Django monolith, Next.js full-stack, Flask + React SPA  
**Chosen:** Flask REST API + React (Vite) SPA  
**Why:** Clear separation for the live session (trace import logic in Python, UI in React). SQLAlchemy gives portable relational schema (SQLite dev, PostgreSQL prod). Fast to iterate with AI assistance.

## 2. Database: Relational only (SQLite / PostgreSQL)

**Options:** MongoDB, Firebase, SQLite, PostgreSQL  
**Chosen:** SQLite locally, PostgreSQL on Render  
**Why:** Assignment requires relational DBs. Expenses, splits, memberships, and settlements are inherently relational with FK integrity.

## 3. USD → INR Conversion Rate

**Options:** Live API rate, user-entered rate per expense, fixed configurable rate  
**Chosen:** Fixed rate via `USD_TO_INR_RATE` env var (default 83.0)  
**Why:** Priya's concern is that $1 ≠ ₹1. A fixed documented rate is auditable and explainable in the live session. Live rates add API dependency and historical ambiguity for Feb–Apr 2026 expenses.

## 4. Negative Amounts

**Options:** Reject as error, treat as separate refund expense, invert payer  
**Chosen:** Import as expense with negative `amount_inr`  
**Why:** Parasailing refund is clearly a reversal of cost. Negative amount reduces the payer's net balance while splits still apply proportionally.

## 5. Duplicate Handling

**Options:** Merge amounts, keep last, keep first, ask user synchronously  
**Chosen:** Keep first occurrence; skip subsequent duplicates. Conflicting amounts flagged as `DUPLICATE_CONFLICT`.  
**Why:** Meera wants approval before deletes. Auto-skip with audit trail satisfies "detect + surface + handle with documented policy."

## 6. Settlement Detection

**Options:** Manual category, keyword heuristics, separate CSV column  
**Chosen:** Keyword heuristic (`paid`, `back`, `settlement`) + empty split_type  
**Why:** Row 14 has no split_type and description says "paid back." Converting to `settlements` table keeps balances correct.

## 7. Missing Payer

**Options:** Skip row, assign to first split member, import with null payer  
**Chosen:** Import with `paid_by_user_id = NULL`, flag for approval, exclude from balance  
**Why:** Silent guess (assigning random member) violates "no silent guess." Null payer makes the gap visible.

## 8. Percentage Splits Not Summing to 100%

**Options:** Reject, use raw percentages, normalize proportionally  
**Chosen:** Normalize proportionally (scale each by 100/sum)  
**Why:** Row 15 notes "percentages might be off." Normalization preserves relative intent while ensuring splits sum to total.

## 9. Membership-Based Split Filtering

**Options:** Trust CSV split_with as-is, filter by membership dates, filter by manual rules  
**Chosen:** Filter split participants by `group_memberships` active on expense date  
**Why:** Sam shouldn't owe March electricity. Meera shouldn't be in April groceries. Membership timeline is explicit and traceable.

## 10. Balance Simplification (Aisha's Request)

**Options:** Show raw pairwise debts, greedy simplification, minimum-cash-flow algorithm  
**Chosen:** Greedy simplify (match largest debtor to largest creditor)  
**Why:** Produces "one number per person" — who pays whom, how much. Good enough for flatmate scale (~6 people).

## 11. Expense Breakdown (Rohan's Request)

**Options:** Summary only, per-expense drill-down API  
**Chosen:** `/balances/<user_id>` endpoint returning every expense line with paid/share/net  
**Why:** Directly answers "show me exactly which expenses make up ₹2,300."

## 12. Authentication

**Options:** OAuth, magic link, email/password JWT  
**Chosen:** JWT email/password  
**Why:** Assignment minimum is login module. JWT is stateless and simple for SPA.

## 13. Ambiguous Dates (04-05-2026)

**Options:** MM-DD (US), DD-MM (India), reject  
**Chosen:** DD-MM-YYYY (Indian flatmates)  
**Why:** Context (Indian city, INR default) strongly suggests day-first. Documented in anomaly report.

## 14. Unknown Split Members (Kabir)

**Options:** Create guest user, exclude and redistribute, fail import  
**Chosen:** Exclude and redistribute among known members  
**Why:** Kabir is a one-day guest not in the flat. Creating a user would skew long-term balances.

## 15. Frontend Serving in Production

**Options:** Separate frontend deploy, CDN, serve from Flask  
**Chosen:** Build React to `frontend/dist`, serve via Flask catch-all route  
**Why:** Single deploy URL for assignment deliverable.
