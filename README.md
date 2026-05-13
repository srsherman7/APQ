# AWS Cloud Practitioner Exam Practice Application

A full-stack web application for preparing for the AWS Cloud Practitioner certification exam. It presents adaptive questions that adjust difficulty based on your performance, provides immediate feedback with memory techniques and IT-context mappings, tracks your progress over time, and offers a focused drill mode for weak areas.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Question Bank](#question-bank)
- [Adding Questions](#adding-questions)
- [Production Notes](#production-notes)
- [Screen Shots](#screen-shots)

---

## Features

- **Adaptive difficulty** — questions start at level 2 and adjust ±1 based on each answer (range 1–5)
- **Immediate feedback** — correct answer, explanation, memory technique, and IT-to-AWS context mapping after every question
- **Session persistence** — progress is saved automatically; resume where you left off after closing the browser
- **Performance dashboard** — overall score, per-topic breakdown, weak area identification, and session history
- **Drill mode** — focuses practice on topics where your score is below the proficiency threshold
- **Study materials** — on-demand study guides (definitions, use cases, exam scenarios, comparison tables) and pre-generated cheatsheets for all four exam domains
- **Responsive UI** — works on desktop, tablet, and mobile (375 px and up)
- **Auth** — registration, login with rate limiting (5 attempts / 15 min), 24-hour session tokens

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 19, Angular Material 19, RxJS 7.8, TypeScript 5.7 |
| Backend | Python 3.10+, Flask 3.0, SQLAlchemy 2.0, Flask-Login 0.6 |
| Database | SQLite (development) / PostgreSQL (production) |
| Auth | bcrypt password hashing, Bearer token sessions |

---

## Project Structure

```
APQ/
├── start.ps1                   # One-command launcher (Windows PowerShell)
│
├── backend/
│   ├── app.py                  # Flask application factory
│   ├── config.py               # Dev / test / prod configuration classes
│   ├── extensions.py           # SQLAlchemy + Flask-Login instances
│   ├── requirements.txt
│   ├── .env.example            # Environment variable template
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py             # User accounts
│   │   ├── question.py         # Question pool
│   │   ├── session.py          # Practice sessions
│   │   ├── question_attempt.py # Per-answer records
│   │   └── user_profile.py     # Aggregated performance data
│   │
│   ├── routes/                 # Flask blueprints (API endpoints)
│   │   ├── auth.py             # /api/register, /api/login, /api/logout, /api/health
│   │   ├── session.py          # /api/session/*
│   │   ├── question.py         # /api/question/*
│   │   ├── analytics.py        # /api/analytics/*
│   │   ├── drill.py            # /api/drill/*
│   │   ├── study.py            # /api/study/*
│   │   └── admin.py            # /api/questions/*
│   │
│   ├── services/               # Business logic
│   │   ├── auth_service.py
│   │   ├── question_engine.py
│   │   ├── adaptive_system.py
│   │   ├── feedback_service.py
│   │   ├── session_manager.py
│   │   ├── analytics_engine.py
│   │   ├── study_guide_generator.py
│   │   └── question_parser.py
│   │
│   ├── middleware/
│   │   └── auth.py             # Bearer token validation decorator
│   │
│   ├── seed_data/
│   │   ├── questions.json      # 73 seed questions
│   │   └── gen.py              # Script that generated questions.json
│   │
│   └── instance/
│       └── aws_exam_practice.db  # SQLite database (auto-created)
│
└── frontend/
    ├── angular.json
    ├── package.json
    └── src/
        ├── index.html
        ├── main.ts
        ├── styles.scss
        ├── environments/
        │   ├── environment.ts          # apiBaseUrl: http://localhost:5000/api
        │   └── environment.prod.ts
        └── app/
            ├── app.config.ts           # HTTP interceptor, router, animations
            ├── app.routes.ts           # Route definitions + auth guard
            │
            ├── guards/
            │   └── auth.guard.ts       # Redirects unauthenticated users to /login
            │
            ├── services/
            │   ├── auth.service.ts     # register / login / logout / token storage
            │   ├── auth.interceptor.ts # Attaches Bearer token; handles 401 redirect
            │   ├── question.service.ts # getNextQuestion / submitAnswer
            │   ├── session.service.ts  # createSession / restoreSession / saveSession
            │   ├── analytics.service.ts
            │   └── study.service.ts
            │
            └── components/
                ├── login/
                ├── register/
                ├── nav-shell/          # Persistent top nav bar + router outlet
                ├── practice-session/   # Main question → feedback loop (/questions)
                ├── question/           # Single question card with radio options
                ├── feedback/           # Answer result, explanation, memory technique
                ├── analytics-dashboard/
                ├── drill-mode/
                └── study-materials/
```

---

## Prerequisites

| Tool | Minimum version | Check |
|---|---|---|
| Python | 3.10 | `python --version` |
| pip | 23+ | `pip --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |

---

## Quick Start

On Windows, a single PowerShell script handles everything:

```powershell
cd e:\DevEnv\APQ
.\start.ps1
```

The script will:
1. Install Python dependencies (`pip install -r requirements.txt`)
2. Install Node dependencies if `node_modules` is missing (`npm install`)
3. Create the SQLite database tables
4. Seed the database with 73 questions (skips any already imported)
5. Open two new terminal windows — one for the backend, one for the frontend

Wait about 10 seconds for the Angular compiler, then open:

```
http://localhost:4200
```

Register a new account and start practising.

---

## Manual Setup

If you prefer to run each part yourself, or are on macOS/Linux:

### Backend

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Initialise the database
python -c "
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    db.create_all()
print('Database ready')
"

# Seed questions
python -c "
import json
from app import create_app
from extensions import db
from models.question import Question

app = create_app()
with app.app_context():
    with open('seed_data/questions.json', encoding='utf-8') as f:
        questions = json.load(f)
    count = 0
    for q in questions:
        if not Question.query.filter_by(question_text=q['question_text']).first():
            db.session.add(Question(**{k: q[k] for k in q}, is_active=True))
            count += 1
    db.session.commit()
    print(f'Seeded {count} questions')
"

# Start the server
python app.py
# Runs on http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm start
# Runs on http://localhost:4200
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask secret key — **change in production** |
| `DATABASE_URI` | `sqlite:///aws_exam_practice.db` | SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:4200` | Comma-separated list of allowed origins |
| `SESSION_COOKIE_SECURE` | `False` | Set to `True` in production (requires HTTPS) |

To use PostgreSQL instead of SQLite:

```
DATABASE_URI=postgresql://user:password@localhost:5432/aws_exam_practice
```

Then uncomment `psycopg2-binary` in `requirements.txt` and reinstall.

---

## API Reference

All endpoints except `POST /api/register`, `POST /api/login`, and `GET /api/health` require:

```
Authorization: Bearer <session_token>
```

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register` | Create a new account `{ username, email, password }` |
| `POST` | `/api/login` | Authenticate `{ username, password }` → returns `session_token` |
| `POST` | `/api/logout` | Invalidate the current session token |
| `GET` | `/api/health` | Health check — returns `{ status: "ok" }` |

### Session

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/session/new` | Start a new practice session |
| `GET` | `/api/session/restore` | Restore the most recent active session |
| `POST` | `/api/session/save` | Save session state `{ session_id, state }` |

### Questions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/question/next` | Get next question `?session_id=&difficulty=` |
| `POST` | `/api/question/answer` | Submit answer `{ session_id, question_id, answer }` → returns feedback + next question |
| `POST` | `/api/question/import` | Batch import questions `{ questions: [...] }` |
| `GET` | `/api/question/filter` | Filter questions `?topic=&difficulty=` |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/profile` | Full performance profile (scores, weak areas, history) |
| `GET` | `/api/analytics/history` | Session history `?limit=20` |

### Drill Mode

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/drill/activate` | Enter drill mode (filters to weak area topics) |
| `POST` | `/api/drill/deactivate` | Exit drill mode |

### Study Materials

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/study/guide/<topic>` | Generate study guide for a topic (up to 30 s) |
| `GET` | `/api/study/cheatsheets` | List all pre-generated cheatsheets |

### Question Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/questions/import` | Batch import via admin route |
| `GET` | `/api/questions/filter` | Filter with full answer data (admin) |

---

## Question Bank

The seed data contains **73 questions** across all four AWS Cloud Practitioner exam domains:

| Topic | Count |
|---|---|
| Technology | 30 |
| Security and Compliance | 17 |
| Billing and Pricing | 15 |
| Cloud Concepts | 11 |
| **Total** | **73** |

Difficulty distribution:

| Level | Count | Description |
|---|---|---|
| 1 | 13 | Foundational definitions |
| 2 | 19 | Core service knowledge |
| 3 | 16 | Applied concepts |
| 4 | 15 | Architecture decisions |
| 5 | 10 | Advanced / multi-service scenarios |

---

## Adding Questions

Questions are stored in `backend/seed_data/questions.json`. Each question follows this schema:

```json
{
  "question_text": "string (max 1000 chars)",
  "options": ["string", "string", "string", "string"],
  "correct_answer": "string (must match one option exactly)",
  "explanation": "string (min 50 chars, max 2000 chars)",
  "memory_technique": "string (max 500 chars)",
  "topic_area": "Cloud Concepts | Security and Compliance | Technology | Billing and Pricing",
  "difficulty_level": 1,
  "it_context_mapping": "string (optional)"
}
```

To import new questions into a running database, POST to `/api/questions/import`:

```bash
curl -X POST http://localhost:5000/api/questions/import \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ "questions": [ { ... } ] }'
```

Or re-run the seed script — it skips questions that already exist (matched by `question_text`).

---

## Production Notes

1. **Secret key** — set a strong random `SECRET_KEY` environment variable; never use the default.
2. **Database** — switch to PostgreSQL by setting `DATABASE_URI`. Uncomment `psycopg2-binary` in `requirements.txt`.
3. **HTTPS** — set `SESSION_COOKIE_SECURE=True` and serve behind a reverse proxy (nginx, Caddy).
4. **CORS** — set `CORS_ORIGINS` to your frontend's production domain.
5. **WSGI server** — replace `python app.py` with Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
   ```
6. **Frontend build** — serve the production build via nginx:
   ```bash
   cd frontend
   npm run build
   # Output in frontend/dist/frontend/browser/
   ```
## Screen Shots
<img width="757" height="573" alt="image" src="https://github.com/user-attachments/assets/3d697589-479a-4603-9ecb-0b492179efc4" />
<img width="2538" height="918" alt="image" src="https://github.com/user-attachments/assets/895ef36b-7a6b-402d-b2b5-0c730e4dd218" />
<img width="2549" height="970" alt="image" src="https://github.com/user-attachments/assets/4a40da09-5dac-4c09-8eae-f6a679e5850d" />
<img width="2536" height="1147" alt="image" src="https://github.com/user-attachments/assets/43d07c66-1d3f-4e7d-afce-ddad8d0d710d" />




