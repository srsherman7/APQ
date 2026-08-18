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
| AWS Developer Associate Exam Guide | https://aws.amazon.com/certification/certified-developer-associate/ |
| AWS ML Specialty Exam Guide | https://aws.amazon.com/certification/certified-machine-learning-specialty/ |
| AWS Security Specialty Exam Guide | https://aws.amazon.com/certification/certified-security-specialty/ |
| AWS Skill Builder (free courses) | https://skillbuilder.aws/ |
| AWS Documentation | https://docs.aws.amazon.com/ |
| AWS Whitepapers & Guides | https://aws.amazon.com/whitepapers/ |
| AWS Official Practice Exams | https://aws.amazon.com/certification/certification-prep/ |

**Sources Used for Questions:**
- Official AWS Exam Guides (CLF-C02, DVA-C02, MLS-C01, SCS-C02)
- AWS Service Documentation and FAQs
- AWS Whitepapers (Security Best Practices, Well-Architected Framework, etc.)
- AWS Security, Identity, & Compliance service pages
- Official AWS training materials and sample questions

**Quality Assurance:**
- All exam configurations match official AWS parameters (question count, time limits, passing scores)
- Answer positions randomized using Fisher-Yates shuffle to prevent position bias
- Option lengths balanced to eliminate "longest answer is correct" patterns
- Maximum 3 consecutive answers in same position (industry standard)
- All questions include detailed explanations and memory techniques

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
- **1,062 total questions across 4 modules** — balanced answer options, shuffled positions, quality-assured
- **Timed exam mode** — simulates the real exam (question count, time limit, and passing score configured per module)
- **Adaptive difficulty** — starts at level 2, adjusts ±1 per answer (range 1–5)
- **Randomised options** — answer positions shuffled on every serve; distractors balanced in length
- **Immediate feedback** — correct answer, explanation, memory technique, and IT-context mapping
- **Performance dashboard** — per-module scores, topic breakdown, weak areas, unified session/exam history
- **Drill mode** — per-module focused practice on topics below 70% (requires ≥5 attempts)
- **Study materials** — per-module study guides and cheatsheets stored in the database (not hardcoded)
- **Module selection** — after login, choose which certification to practice; switch anytime via profile menu
- **Self-service module creation** — create custom modules via API or standalone preparation tool
- **Module import/export** — export modules as JSON, import into other instances
- **Reset progress** — clear all history per-user from Settings (profile menu)
- **Session persistence** — progress saves automatically; resume where you left off
- **Single-port deployment** — Flask serves both the API and Angular production build on port 4201
- **LAN/external access** — auto-detects network IP; works through DDNS with port forwarding
- **Render.com ready** — includes `build.sh` for one-click cloud deployment
- **Responsive UI** — works on desktop, tablet, and mobile (375px+)
- **Auth** — registration, login with rate limiting (5 attempts / 15 min), 24-hour session tokens

---

## Modules

| Module | Questions | Exam Format | Pass Score | Study Guides |
|---|---|---|---|---|
| AWS Cloud Practitioner (CLF-C02) | 472 | 65 questions / 90 min | 70% | 4 guides, 6 cheatsheets |
| AWS Developer Associate (DVA-C02) | 257 | 65 questions / 130 min | 72% | 4 guides, 6 cheatsheets |
| AWS Machine Learning Specialty (MLS-C01) | 285 | 85 questions / 170 min | 75% | 4 guides, 5 cheatsheets |
| AWS Security Specialty (SCS-C02) | 52 | 65 questions / 170 min | 75% | 5 domains, cheatsheet |

Each module has:
- Independent question pool across all difficulty levels (1–5)
- Module-specific topic areas and study guides
- Separate session history, analytics, and drill mode
- Configurable exam parameters (question count, time limit, passing score)
- Exam configurations verified against official AWS parameters

---
