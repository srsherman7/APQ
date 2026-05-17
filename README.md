# AWS Cloud Practitioner Exam Practice Application

A full-stack web application for preparing for the AWS Cloud Practitioner certification exam. Features an adaptive question system that adjusts difficulty based on performance, immediate feedback with memory techniques and IT-context mappings, progress tracking, drill mode for weak areas, and study materials — all served from a single port with no external dependencies.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [External Access](#external-access)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Question Bank](#question-bank)
- [Adding Questions](#adding-questions)
- [Production Notes](#production-notes)
- [Screenshots](#screenshots)

---

## Features

- **472 curated questions** — covering all four exam domains with balanced answer options (no length-based guessing)
- **Adaptive difficulty** — starts at level 2, adjusts ±1 per answer (range 1–5)
- **Randomised options** — answer positions are shuffled on every question serve
- **Immediate feedback** — correct answer, explanation, memory technique, and IT-to-AWS context mapping
- **Session persistence** — progress saves automatically; resume where you left off
- **Performance dashboard** — overall score, per-topic breakdown, weak area identification, session history
- **Drill mode** — focused practice on topics where your score is below 70% (requires ≥5 attempts in a topic)
- **Study materials** — on-demand study guides and pre-generated cheatsheets for all exam domains
- **Reset progress** — clear all history and start fresh from the Settings menu
- **Single-port deployment** — Flask serves both the API and the Angular production build on one port (4201)
- **LAN/external access** — auto-detects your network IP; works through DDNS with port forwarding
- **Responsive UI** — works on desktop, tablet, and mobile (375px and up)
- **Auth** — registration, login with rate limiting (5 attempts / 15 min), 24-hour session tokens

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 19, Angular Material 19, RxJS 7.8, TypeScript 5.7 |
| Backend | Python 3.10+, Flask 3.0, SQLAlchemy 2.0, Flask-Login 0.6 |
| Database | SQLite (development) / PostgreSQL (production) |
| Auth | bcrypt password hashing, Bearer token sessions |
| Deployment | Single process — Flask serves API + static Angular build |

---

## Project Structure

```
APQ/
├── start.ps1                   # One-command launcher (Windows PowerShell)
├── LICENSE                     # MIT License
├── README.md
│
├── backend/
│   ├── app.py                  # Flask app factory (serves API + Angular static files)
│   ├── config.py               # Dev / test / prod configuration
│   ├── extensions.py           # SQLAlchemy + Flask-Login instances
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── question.py         # Includes option shuffling on serve
│   │   ├── session.py
│   │   ├── question_attempt.py
│   │   └── user_profile.py
│   │
│   ├── routes/                 # Flask blueprints (API endpoints)
│   │   ├── auth.py             # /api/register, /api/login, /api/logout
│   │   ├── session.py          # /api/session/* (includes /reset)
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
│   │   └── auth.py
│   │
│   ├── seed_data/
│   │   ├── questions.json      # 472 balanced questions
│   │   ├── gen.py              # Question generator script
│   │   └── balance_options.py  # Option length balancing utility
│   │
│   └── instance/
│       └── aws_exam_practice.db
│
└── frontend/
    ├── angular.json
    ├── package.json
    ├── vite.config.js          # Allows external hostname access
    └── src/
        ├── index.html
        ├── main.ts
        ├── styles.scss
        ├── environments/
        │   ├── environment.ts
        │   └── environment.prod.ts   # Uses relative /api path
        └── app/
            ├── app.config.ts
            ├── app.routes.ts
            ├── guards/
            │   └── auth.guard.ts
            ├── services/
            │   ├── auth.service.ts
            │   ├── auth.interceptor.ts
            │   ├── question.service.ts
            │   ├── session.service.ts
            │   ├── analytics.service.ts
            │   └── study.service.ts
            └── components/
                ├── login/
                ├── register/
                ├── nav-shell/              # Top nav bar + router outlet
                ├── practice-session/       # Question → feedback loop
                ├── question/
                ├── feedback/
                ├── analytics-dashboard/
                ├── drill-mode/
                ├── study-materials/
                └── admin-panel/            # Settings (reset progress)
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

```powershell
cd e:\DevEnv\APQ
.\start.ps1
```

The script will:
1. Install Python dependencies
2. Install Node dependencies (first run only)
3. Build the Angular frontend for production
4. Create database tables and seed 472 questions
5. Launch Flask in a new terminal window (serves everything on port 4201)

Open your browser to the URL shown in the terminal (typically `http://localhost:4201` or your LAN IP).

Register a new account and start practising.

---

## Manual Setup

For macOS/Linux or if you prefer running each step yourself:

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt

# Initialise database + seed questions
python -c "
import json
from app import create_app
from extensions import db
from models.question import Question

app = create_app()
with app.app_context():
    db.create_all()
    with open('seed_data/questions.json', encoding='utf-8') as f:
        questions = json.load(f)
    count = 0
    for q in questions:
        if not Question.query.filter_by(question_text=q['question_text']).first():
            db.session.add(Question(
                question_text=q['question_text'], options=q['options'],
                correct_answer=q['correct_answer'], explanation=q['explanation'],
                memory_technique=q['memory_technique'], topic_area=q['topic_area'],
                difficulty_level=q['difficulty_level'],
                it_context_mapping=q.get('it_context_mapping'), is_active=True
            ))
            count += 1
    db.session.commit()
    print(f'Seeded {count} questions. Total: {Question.query.count()}')
"
```

### Frontend (build only — Flask serves the output)

```bash
cd frontend
npm install
npx ng build --configuration production
```

### Run

```bash
cd backend
python app.py
# Serves everything on http://localhost:4201
```

---

## External Access

The app runs on a single port (4201). To access from other devices:

1. **LAN access** — `start.ps1` auto-detects your LAN IP and configures CORS. Other devices on your network can access `http://<your-ip>:4201`.

2. **Internet access via DDNS** — forward port 4201 in your router to your machine's LAN IP. The `vite.config.js` allows any hostname, and Flask's CORS is configured by `start.ps1`.

3. **Override the bind IP** — `.\start.ps1 -BindIP 0.0.0.0` to listen on all interfaces.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and adjust as needed.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-in-production` | Flask secret key — **change in production** |
| `DATABASE_URI` | `sqlite:///aws_exam_practice.db` | SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:4200` | Comma-separated allowed origins (overridden by `start.ps1`) |
| `SESSION_COOKIE_SECURE` | `False` | Set to `True` in production (requires HTTPS) |

For PostgreSQL:
```
DATABASE_URI=postgresql://user:password@localhost:5432/aws_exam_practice
```
Uncomment `psycopg2-binary` in `requirements.txt` and reinstall.

---

## API Reference

All endpoints except `POST /api/register`, `POST /api/login`, and `GET /api/health` require:
```
Authorization: Bearer <session_token>
```

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register` | Create account `{ username, email, password }` |
| `POST` | `/api/login` | Authenticate `{ username, password }` → `session_token` |
| `POST` | `/api/logout` | Invalidate session token |
| `GET` | `/api/health` | Health check |

### Session

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/session/new` | Start a new practice session |
| `GET` | `/api/session/restore` | Restore most recent active session |
| `POST` | `/api/session/save` | Save session state |
| `POST` | `/api/session/reset` | Delete all progress for the current user |

### Questions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/question/next` | Next question `?session_id=&difficulty=` |
| `POST` | `/api/question/answer` | Submit answer → feedback + next question |
| `POST` | `/api/question/import` | Batch import questions |
| `GET` | `/api/question/filter` | Filter by topic/difficulty |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/profile` | Performance profile (scores, weak areas, history) |
| `GET` | `/api/analytics/history` | Session history `?limit=20` |

### Drill Mode

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/drill/activate` | Enter drill mode (weak area topics) |
| `POST` | `/api/drill/deactivate` | Exit drill mode |

### Study Materials

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/study/guide/<topic>` | Generate study guide (up to 30s) |
| `GET` | `/api/study/cheatsheets` | List pre-generated cheatsheets |

---

## Question Bank

**472 curated questions** across all four AWS Cloud Practitioner exam domains:

| Topic | Count |
|---|---|
| Technology | 157 |
| Billing and Pricing | 104 |
| Security and Compliance | 103 |
| Cloud Concepts | 108 |
| **Total** | **472** |

Difficulty distribution:

| Level | Count | Description |
|---|---|---|
| 1 | 60 | Foundational definitions |
| 2 | 108 | Core service knowledge |
| 3 | 113 | Applied concepts and comparisons |
| 4 | 115 | Architecture decisions and trade-offs |
| 5 | 76 | Advanced multi-service scenarios |

### Anti-pattern protections

- **Option shuffling** — answer positions are randomised on every serve
- **Balanced option lengths** — distractors are similar in length to the correct answer (correct answer is longest only ~10% of the time, matching natural distribution)

---

## Adding Questions

Questions follow this schema:

```json
{
  "question_text": "string (max 1000 chars)",
  "options": ["option A", "option B", "option C", "option D"],
  "correct_answer": "must match one option exactly",
  "explanation": "string (min 50 chars)",
  "memory_technique": "mnemonic or memory aid",
  "topic_area": "Cloud Concepts | Security and Compliance | Technology | Billing and Pricing",
  "difficulty_level": 1-5,
  "it_context_mapping": "traditional IT equivalent (optional)"
}
```

**Tip:** Keep all four options similar in length and detail. Run `python seed_data/balance_options.py` after adding questions to automatically balance any length discrepancies.

To import via API:
```bash
curl -X POST http://localhost:4201/api/questions/import \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{ "questions": [ { ... } ] }'
```

---

## Production Notes

1. **Secret key** — set a strong random `SECRET_KEY`; never use the default
2. **Database** — switch to PostgreSQL via `DATABASE_URI` for concurrent users
3. **HTTPS** — set `SESSION_COOKIE_SECURE=True` and serve behind a reverse proxy
4. **WSGI server** — replace `python app.py` with Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:4201 "app:create_app()"
   ```
5. **Port** — the app runs on port 4201 by default (configurable in `app.py`)

---

## Screenshots

<img width="757" height="573" alt="image" src="https://github.com/user-attachments/assets/3d697589-479a-4603-9ecb-0b492179efc4" />
<img width="1359" height="853" alt="{0967A806-69D4-4E89-A9DE-F2EFE1BB0135}" src="https://github.com/user-attachments/assets/20a86dc4-41f1-49a6-ba96-48d39d6c955c" />
<img width="1360" height="848" alt="{6D643D9F-7661-45A2-83AE-9658090832F9}" src="https://github.com/user-attachments/assets/ad434fd1-697d-438a-9e3b-12cd2d63660f" />
<img width="1363" height="850" alt="{DE632C62-7F7F-49A8-8880-9D85A7A25C51}" src="https://github.com/user-attachments/assets/a5b6e3a6-b729-44e3-8038-a7b4b3f7bcc7" />
<img width="1386" height="413" alt="{A7CCEFC9-6B5E-471D-A177-A00C7EE04927}" src="https://github.com/user-attachments/assets/58779f2a-2ecd-4a43-beee-e26aafcc64b3" />
<img width="1390" height="946" alt="{9B3F0FB9-B96B-457F-B4A3-A666E26959E1}" src="https://github.com/user-attachments/assets/5d27effa-4af9-47de-8bfc-c746f5f0245c" />
