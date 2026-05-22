# AWS Certification Practice Platform

A modular, full-stack learning management system for preparing for AWS certification exams. Each certification is a self-contained module with its own question bank, exam format, study materials, and progress tracking — all served from a single port with no external dependencies.

---

## Disclaimer

**This application is not affiliated with, endorsed by, or verified by Amazon Web Services (AWS).** It is an independent, personal study tool built for self-directed exam preparation.

The question content is aggregated from publicly available AWS documentation, whitepapers, FAQs, and official exam guides, then compiled into a structured format for adaptive practice. While every effort has been made to ensure accuracy, this tool **should not be considered a replacement for official AWS training, courses, or practice exams.**

### Official AWS Resources

| Resource | Link |
|---|---|
| AWS Cloud Practitioner Exam Guide | https://aws.amazon.com/certification/certified-cloud-practitioner/ |
| AWS ML Specialty Exam Guide | https://aws.amazon.com/certification/certified-machine-learning-specialty/ |
| AWS Skill Builder (free courses) | https://skillbuilder.aws/ |
| AWS Documentation | https://docs.aws.amazon.com/ |
| AWS Whitepapers & Guides | https://aws.amazon.com/whitepapers/ |
| AWS Official Practice Exams | https://aws.amazon.com/certification/certification-prep/ |

### Future Vision

This application is architected as a general-purpose adaptive learning system. The question engine, adaptive difficulty, session management, analytics, and drill mode are all content-agnostic — they work with any subject matter that can be expressed as multiple-choice questions. Adding a new certification module requires only creating questions and a module configuration — no code changes.

---

## Table of Contents

- [Features](#features)
- [Modules](#modules)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Setup](#manual-setup)
- [External Access](#external-access)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Adding a New Module](#adding-a-new-module)
- [Question Schema](#question-schema)
- [Production Notes](#production-notes)
- [Screenshots](#screenshots)

---

## Features

- **Modular architecture** — each certification is an independent module with its own questions, exam format, study materials, and progress tracking
- **472 Cloud Practitioner questions + 285 ML Specialty questions** — balanced answer options, shuffled positions
- **Timed exam mode** — simulates the real exam (question count, time limit, and passing score configured per module)
- **Adaptive difficulty** — starts at level 2, adjusts ±1 per answer (range 1–5)
- **Randomised options** — answer positions shuffled on every serve; distractors balanced in length
- **Immediate feedback** — correct answer, explanation, memory technique, and IT-context mapping
- **Performance dashboard** — per-module scores, topic breakdown, weak areas, unified session/exam history
- **Drill mode** — per-module focused practice on topics below 70% (requires ≥5 attempts)
- **Study materials** — per-module study guides and cheatsheets with definitions, use cases, exam scenarios, and comparison tables
- **Module selection** — after login, choose which certification to practice; switch anytime via profile menu
- **Reset progress** — clear all history per-user from Settings (profile menu)
- **Session persistence** — progress saves automatically; resume where you left off
- **Single-port deployment** — Flask serves both the API and Angular production build on port 4201
- **Turso database support** — optional remote libSQL for cloud deployments (falls back to local SQLite)
- **LAN/external access** — auto-detects network IP; works through DDNS with port forwarding
- **Render.com ready** — includes `build.sh` for one-click cloud deployment
- **Responsive UI** — works on desktop, tablet, and mobile (375px+)
- **Auth** — registration, login with rate limiting (5 attempts / 15 min), 24-hour session tokens

---

## Modules

| Module | Questions | Exam Format | Pass Score |
|---|---|---|---|
| AWS Cloud Practitioner | 472 | 65 questions / 90 min | 70% |
| AWS Machine Learning Specialty | 285 | 85 questions / 170 min | 75% |

Each module has:
- Independent question pool across all difficulty levels (1–5)
- Module-specific topic areas and study guides
- Separate session history, analytics, and drill mode
- Configurable exam parameters (question count, time limit, passing score)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Angular 19, Angular Material 19, RxJS 7.8, TypeScript 5.7 |
| Backend | Python 3.10+, Flask 3.0, SQLAlchemy 2.0, Flask-Login 0.6 |
| Database | SQLite (local) / Turso libSQL (cloud) / PostgreSQL (production) |
| Auth | bcrypt password hashing, Bearer token sessions |
| Deployment | Single process — Flask serves API + static Angular build |

---

## Project Structure

```
APQ/
├── start.ps1                   # One-command launcher (Windows PowerShell)
├── build.sh                    # Render.com build script
├── render.yaml                 # Render deployment config
├── LICENSE                     # MIT License
├── README.md
│
├── backend/
│   ├── app.py                  # Flask app factory (serves API + Angular static files)
│   ├── config.py               # Configuration with Turso/SQLite/PostgreSQL support
│   ├── extensions.py           # SQLAlchemy + Flask-Login instances
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── models/
│   │   ├── module.py           # Module definition (name, exam config, topics)
│   │   ├── user.py
│   │   ├── question.py         # Module-scoped, option shuffling on serve
│   │   ├── session.py          # Module-scoped practice sessions
│   │   ├── question_attempt.py
│   │   ├── user_profile.py     # Per-user per-module analytics
│   │   └── exam_attempt.py     # Module-scoped timed exams
│   │
│   ├── routes/
│   │   ├── modules.py          # GET /api/modules/ — list/get modules
│   │   ├── auth.py             # /api/register, /api/login, /api/logout
│   │   ├── session.py          # /api/session/* (new, restore, save, reset)
│   │   ├── question.py         # /api/question/* (next, answer, import, filter)
│   │   ├── analytics.py        # /api/analytics/* (profile, history)
│   │   ├── drill.py            # /api/drill/* (activate, deactivate)
│   │   ├── exam.py             # /api/exam/* (start, answer, submit, history, result)
│   │   ├── study.py            # /api/study/* (guide, cheatsheets)
│   │   └── admin.py            # /api/questions/* (import, filter, reseed)
│   │
│   ├── services/
│   │   ├── question_engine.py      # Module-scoped question selection
│   │   ├── adaptive_system.py      # Difficulty adjustment logic
│   │   ├── feedback_service.py     # Explanation + memory technique generation
│   │   ├── session_manager.py      # Module-aware session lifecycle
│   │   ├── analytics_engine.py     # Module-scoped analytics + history
│   │   ├── auth_service.py         # Registration, login, token management
│   │   ├── study_guide_generator.py # Per-module study content (CP + ML)
│   │   └── question_parser.py      # JSON import/validation
│   │
│   ├── middleware/
│   │   └── auth.py
│   │
│   └── seed_data/
│       ├── questions.json          # 472 Cloud Practitioner questions
│       ├── ml_questions.json       # 285 ML Specialty questions
│       ├── gen.py                  # CP question generator
│       ├── ml_questions_gen.py     # ML question generator
│       └── balance_options.py      # Option length balancing utility
│
└── frontend/
    ├── angular.json
    ├── package.json
    ├── vite.config.js
    └── src/app/
        ├── app.routes.ts           # Module selection + protected routes
        ├── guards/auth.guard.ts
        ├── services/
        │   ├── module.service.ts       # Active module state (localStorage)
        │   ├── auth.service.ts
        │   ├── auth.interceptor.ts
        │   ├── question.service.ts
        │   ├── session.service.ts      # Module-aware create/restore
        │   ├── analytics.service.ts    # Module-aware profile/history
        │   └── study.service.ts        # Module-aware cheatsheets
        └── components/
            ├── module-select/          # Module picker (after login)
            ├── nav-shell/              # Dynamic title showing active module
            ├── practice-session/       # Module-scoped question loop
            ├── question/
            ├── feedback/
            ├── analytics-dashboard/    # Module-scoped history + metrics
            ├── drill-mode/             # Module-scoped weak area drilling
            ├── exam-mode/              # Dynamic exam config from module
            ├── study-materials/        # Dynamic topics from module
            ├── login/
            ├── register/
            └── admin-panel/            # Settings (reset progress)
```

---

## Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.10 |
| Node.js | 18 |
| npm | 9 |

---

## Quick Start

```powershell
cd e:\DevEnv\APQ
.\start.ps1
```

The script will:
1. Install Python and Node dependencies
2. Build the Angular frontend for production
3. Create database tables and seed both modules (Cloud Practitioner + ML Specialty)
4. Launch Flask on port 4201

Open `http://localhost:4201`, register, and select a module.

---

## Manual Setup

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Init DB + seed (creates both modules)
python -c "
from app import create_app
from extensions import db
from models.module import Module
from models.question import Question
import json

app = create_app()
with app.app_context():
    db.create_all()
    # Cloud Practitioner module
    if not Module.query.filter_by(slug='cloud-practitioner').first():
        m = Module(slug='cloud-practitioner', name='AWS Cloud Practitioner', icon='cloud',
            exam_question_count=65, exam_time_limit_seconds=5400, exam_passing_score=70.0,
            topic_areas=['Cloud Concepts','Security and Compliance','Technology','Billing and Pricing'])
        db.session.add(m); db.session.commit()
        with open('seed_data/questions.json') as f:
            for q in json.load(f):
                if not Question.query.filter_by(question_text=q['question_text']).first():
                    db.session.add(Question(module_id=m.module_id, **q, is_active=True))
        db.session.commit()
    # ML Specialty module
    if not Module.query.filter_by(slug='ml-specialty').first():
        m = Module(slug='ml-specialty', name='AWS Machine Learning Specialty', icon='psychology',
            exam_question_count=85, exam_time_limit_seconds=10200, exam_passing_score=75.0,
            topic_areas=['Data Engineering','Exploratory Data Analysis','Modeling','ML Implementation and Operations'])
        db.session.add(m); db.session.commit()
        with open('seed_data/ml_questions.json') as f:
            for q in json.load(f):
                if not Question.query.filter_by(question_text=q['question_text']).first():
                    db.session.add(Question(module_id=m.module_id, **q, is_active=True))
        db.session.commit()
    print('Done')
"

# Frontend
cd ../frontend
npm install
npx ng build --configuration production

# Run
cd ../backend
python app.py
# → http://localhost:4201
```

---

## External Access

Single port (4201). For LAN/internet access:
- `start.ps1` auto-detects LAN IP and configures CORS
- `vite.config.js` allows any hostname
- Forward port 4201 in your router for DDNS access

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | dev key | Flask secret — **change in production** |
| `DATABASE_URI` | `sqlite:///aws_exam_practice.db` | Local SQLite fallback |
| `TURSO_DATABASE_URL` | *(empty)* | Turso libSQL URL for cloud DB |
| `TURSO_AUTH_TOKEN` | *(empty)* | Turso auth token |
| `CORS_ORIGINS` | `http://localhost:4201` | Allowed origins |
| `PORT` | `4201` | Server port (Render sets this) |

---

## API Reference

All endpoints except `/api/register`, `/api/login`, `/api/health` require `Authorization: Bearer <token>`.

### Modules
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/modules/` | List all active modules |
| `GET` | `/api/modules/<slug>` | Get module details |

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/register` | Create account |
| `POST` | `/api/login` | Authenticate → session_token |
| `POST` | `/api/logout` | Invalidate token |

### Session
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/session/new` | New session `{ module_id }` |
| `GET` | `/api/session/restore?module_id=` | Restore active session |
| `POST` | `/api/session/save` | Save session state |
| `POST` | `/api/session/reset` | Delete all user progress |

### Questions
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/question/next?session_id=` | Next question (module-scoped) |
| `POST` | `/api/question/answer` | Submit answer → feedback |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/profile?module_id=` | Module-scoped performance |
| `GET` | `/api/analytics/history?module_id=` | Module-scoped session history |

### Drill Mode
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/drill/activate` | Enter drill mode (module-scoped) |
| `POST` | `/api/drill/deactivate` | Exit drill mode |

### Exam Mode
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/exam/start` | Start exam `{ module_id }` |
| `POST` | `/api/exam/answer` | Save answer |
| `POST` | `/api/exam/submit` | Submit for grading |
| `GET` | `/api/exam/history` | Completed exams |
| `GET` | `/api/exam/result/<id>` | Detailed results |

### Study Materials
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/study/guide/<topic>` | Generate study guide |
| `GET` | `/api/study/cheatsheets?module_id=` | Module-scoped cheatsheets |

---

## Adding a New Module

1. Create a question JSON file in `backend/seed_data/`
2. Add a `Module` row to the database:
```python
Module(
    slug='solutions-architect',
    name='AWS Solutions Architect Associate',
    icon='architecture',
    exam_question_count=65,
    exam_time_limit_seconds=7800,  # 130 min
    exam_passing_score=72.0,
    topic_areas=['Design Resilient Architectures', 'Design High-Performing Architectures', 'Design Secure Architectures', 'Design Cost-Optimized Architectures'],
)
```
3. Import questions with `module_id` pointing to the new module
4. Add study guide content to `study_guide_generator.py` for the new topics
5. No frontend code changes needed — the module appears automatically

---

## Question Schema

```json
{
  "question_text": "string (max 1000 chars)",
  "options": ["option A", "option B", "option C", "option D"],
  "correct_answer": "must match one option exactly",
  "explanation": "string (min 50 chars)",
  "memory_technique": "mnemonic or memory aid",
  "topic_area": "must match one of the module's topic_areas",
  "difficulty_level": 1-5,
  "it_context_mapping": "traditional IT equivalent (optional)"
}
```

**Tips:**
- Keep all four options similar in length and detail
- Run `python seed_data/balance_options.py` to auto-balance length discrepancies
- Options are shuffled on every serve — position doesn't matter

---

## Production Notes

1. **Secret key** — set a strong random `SECRET_KEY`
2. **Database** — use Turso (`TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN`) or PostgreSQL (`DATABASE_URI`)
3. **HTTPS** — set `SESSION_COOKIE_SECURE=True` behind a reverse proxy
4. **WSGI** — `gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"`
5. **Render.com** — Build: `chmod +x build.sh && ./build.sh` / Start: `cd backend && gunicorn "app:create_app()" --bind 0.0.0.0:$PORT`

---

## Screenshots

<img width="757" height="573" alt="image" src="https://github.com/user-attachments/assets/3d697589-479a-4603-9ecb-0b492179efc4" />
<img width="1552" height="753" alt="{EFF91A31-5B92-42BF-90B9-A1F635ED34AD}" src="https://github.com/user-attachments/assets/1d349b8f-8a13-42d6-90e4-970db2579c8c" />
<img width="290" height="369" alt="{7F1F6583-FB81-465E-AC17-328D317414E4}" src="https://github.com/user-attachments/assets/f5e00e53-a15f-4a6e-b3b6-c4da57678232" />

<img width="1359" height="853" alt="{0967A806-69D4-4E89-A9DE-F2EFE1BB0135}" src="https://github.com/user-attachments/assets/20a86dc4-41f1-49a6-ba96-48d39d6c955c" />
<img width="1360" height="848" alt="{6D643D9F-7661-45A2-83AE-9658090832F9}" src="https://github.com/user-attachments/assets/ad434fd1-697d-438a-9e3b-12cd2d63660f" />
<img width="1363" height="850" alt="{DE632C62-7F7F-49A8-8880-9D85A7A25C51}" src="https://github.com/user-attachments/assets/a5b6e3a6-b729-44e3-8038-a7b4b3f7bcc7" />
<img width="1386" height="413" alt="{A7CCEFC9-6B5E-471D-A177-A00C7EE04927}" src="https://github.com/user-attachments/assets/58779f2a-2ecd-4a43-beee-e26aafcc64b3" />
<img width="1390" height="946" alt="{9B3F0FB9-B96B-457F-B4A3-A666E26959E1}" src="https://github.com/user-attachments/assets/5d27effa-4af9-47de-8bfc-c746f5f0245c" />
<img width="1485" height="515" alt="{A3609826-0D9A-4616-AB51-904F7ED3430B}" src="https://github.com/user-attachments/assets/43dd8010-8a77-4581-9ffb-0ab63ab7a244" />
<img width="1709" height="979" alt="{33332899-10EF-47FE-BA07-81AF1B50414C}" src="https://github.com/user-attachments/assets/16c06ed5-e282-477c-a68c-0723d7b6d698" />
<img width="1865" height="1086" alt="{1509DE56-F5F5-4323-8050-138C5F02A338}" src="https://github.com/user-attachments/assets/85ab2964-230a-4790-9727-9260c70be080" />

