# BreachAlert — Project 3: Full-Stack with Database

A production-ready REST API with SQLite persistence. All scans, users, and analysis results are now durably stored in a real database. The frontend and API work together seamlessly — no dummy data, fully functional.

## Architecture

```
Frontend (Project 1)          Backend API (Project 3)        Database
  HTML/CSS/JS    ────────→     Flask + SQLAlchemy    ───→   SQLite
  Port 8000                      Port 5000                    breachalert.db
```

## Project structure

```
breachalert-fullstack/
├── app.py                # Flask routes with database integration
├── models.py             # SQLAlchemy ORM models (User, Scan)
├── validators.py         # Request validation (Gatekeeper layer)
├── security_utils.py     # Breach lookup, password analysis
├── test_app.py           # Full test suite (15+ tests)
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup & Run

### 1. Create virtual environment

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
```

On Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize database

```bash
python app.py
```

On first run, it auto-creates the SQLite database and tables. You should see:

```
✓ Database initialized
BreachAlert API (Project 3: Database Integration)
→ http://localhost:5000/api/v1/health
→ SQLite database: breachalert.db
```

Leave this terminal running. In a **second terminal**, start the frontend (Project 1):

```powershell
cd ../breachalert
python server.py
```

Now you have:
- **Frontend:** http://localhost:8000
- **API:** http://localhost:5000
- **Database:** `breachalert.db` (auto-created)

## Database Schema

### Users table

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer | Primary key, auto-increment |
| `email` | String(254) | Unique, indexed. User's email. |
| `created_at` | DateTime | UTC timestamp when user first scanned |

### Scans table

| Column | Type | Notes |
|--------|------|-------|
| `id` | String(36) | Primary key, UUID |
| `user_id` | Integer | Foreign key → users.id |
| `email_checked` | String(254) | Email that was scanned (denormalized for easy queries) |
| `security_score` | Integer | 0-100 score |
| `breach_found` | Boolean | Was any breach detected? |
| `breach_count` | Integer | How many breaches? |
| `breach_data` | JSON | Array of breach objects |
| `password_strength_score` | Integer | 0-100, or NULL if no password tested |
| `password_strength_label` | String(20) | "strong", "moderate", "weak", "very_weak" |
| `password_entropy_bits` | Float | Entropy calculation |
| `password_flags` | JSON | Array: "too_short", "common_password", etc. |
| `created_at` | DateTime | UTC timestamp |

**Indexes:** `user_id`, `email_checked`, `created_at` for fast queries.

## API Endpoints (Enhanced with Database)

### 1. **GET /api/v1/health**
Health check + database status.

```bash
curl http://localhost:5000/api/v1/health
```

Response:
```json
{
  "status": "ok",
  "service": "BreachAlert API",
  "version": "2.0.0",
  "database": "SQLite",
  "time": "2026-07-15T10:30:45.123456+00:00"
}
```

---

### 2. **POST /api/v1/scans** (Creates a scan, saves to DB)

```bash
curl -X POST http://localhost:5000/api/v1/scans \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "YourPassword123!"
  }'
```

Response (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email_checked": "you@example.com",
  "score": 75,
  "breach": {
    "email_checked": "you@example.com",
    "breach_found": false,
    "breach_count": 0,
    "breaches": []
  },
  "password_analysis": {
    "score": 85,
    "strength_label": "strong",
    "entropy_bits": 62.4,
    "flags": []
  },
  "created_at": "2026-07-15T10:30:45.123456+00:00"
}
```

The scan is now **permanently saved** in the database.

---

### 3. **GET /api/v1/scans/{id}** (Retrieve from DB)

```bash
curl http://localhost:5000/api/v1/scans/550e8400-e29b-41d4-a716-446655440000
```

Returns the exact same structure as the POST response.

---

### 4. **GET /api/v1/users/{email}/scans** (NEW: Get all scans for a user)

```bash
curl http://localhost:5000/api/v1/users/you@example.com/scans
```

Response (200):
```json
{
  "email": "you@example.com",
  "scans_count": 3,
  "user_created_at": "2026-07-15T10:15:00.000000+00:00",
  "scans": [
    { /* scan 1 */ },
    { /* scan 2 */ },
    { /* scan 3 */ }
  ]
}
```

Shows the **complete scan history** for a user — tracked over time, scored, and comparable.

---

### 5. **POST /api/v1/passwords/analyze** (Stateless, not persisted)

```bash
curl -X POST http://localhost:5000/api/v1/passwords/analyze \
  -H "Content-Type: application/json" \
  -d '{"password": "hunter2"}'
```

Response (200):
```json
{
  "score": 10,
  "strength_label": "very_weak",
  "entropy_bits": 15.2,
  "flags": ["common_password", "too_short"]
}
```

This endpoint does NOT create a scan record — it's pure analysis, no persistence.

---

### 6. **GET /api/v1/stats** (NEW: Real database stats)

```bash
curl http://localhost:5000/api/v1/stats
```

Response (200):
```json
{
  "total_scans": 42,
  "breaches_found": 8,
  "unique_users": 31,
  "average_score": 68.5,
  "timestamp": "2026-07-15T10:35:20.123456+00:00"
}
```

Numbers are **live from the database**, not mocked.

---

## Run the test suite

```bash
python -m unittest test_app.py -v
```

All 20+ tests should pass:
- User creation on first scan
- Scan persistence and retrieval
- Breach detection with data storage
- Password analysis with history
- Stats aggregation from database
- Error handling (400, 404, 429)

---

## Connecting the frontend

In your Project 1 frontend's `script.js`, update the scan form handler:

```javascript
const response = await fetch('http://localhost:5000/api/v1/scans', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email: emailValue,
    password: passwordValue  // optional
  })
});

if (response.ok) {
  const scan = await response.json();
  // Update the frontend with scan.score, scan.breach, etc.
  // This scan is now permanently saved in the database
} else {
  const { error } = await response.json();
  // Show error.message to the user
}
```

The frontend now talks to a **real, persistent API** instead of a simulation.

---

## Database management

### Reset the database (delete all data)

```bash
python -c "from app import app; app.cli.commands['reset_db'].callback()"
```

Or delete `breachalert.db` and restart the server.

### Seed demo data

```bash
python -c "from app import app; app.cli.commands['seed_demo'].callback()"
```

Creates demo users so you can test multi-user scenarios.

---

## Architecture decisions

1. **SQLite** — Perfect for Project 3's scope. No external database server to manage. If this scales, swapping to PostgreSQL is one line in the config.

2. **SQLAlchemy ORM** — Models are Pythonic, migrations are easy (Flask-Migrate ready), and routes are decoupled from SQL.

3. **Users table** — Enables user history, aggregate stats, and future features like alerts ("your email appeared in a new breach").

4. **JSON columns** — `breach_data` and `password_flags` are stored as JSON, so you can query/analyze them later without changing the schema.

5. **No password storage** — Raw passwords are never persisted. Only the analysis (flags, score, entropy) is saved.

6. **Indexes on hot columns** — `user_id`, `email_checked`, `created_at` for fast queries even as the database grows.

---

## Deployment notes

For real deployment:
- Replace `app.run(debug=True)` with a WSGI server like Gunicorn
- Use PostgreSQL instead of SQLite (change `SQLALCHEMY_DATABASE_URI`)
- Store the database on persistent storage (not the app container)
- Add rate limiting middleware (Redis-backed, not in-memory)
- Enable HTTPS + CORS security headers
- Use environment variables for secrets

For now, this setup is perfect for development and a portfolio project.

---

## Troubleshooting

**`ImportError: No module named 'sqlalchemy'`**
Your venv isn't activated or requirements weren't installed. Run:
```bash
pip install -r requirements.txt
```

**`database is locked` error**
You have two instances trying to write simultaneously. Stop all servers, delete `breachalert.db`, and restart fresh.

**Frontend can't reach API / CORS error**
API must be running on port 5000. Check: `http://localhost:5000/api/v1/health` works in your browser. CORS is enabled for `*` in development — tighten it to your frontend URL before deploying.

**Tests fail**
Make sure no API server is running (it locks the database). Run tests with a fresh in-memory SQLite: `python -m unittest test_app.py -v`.
