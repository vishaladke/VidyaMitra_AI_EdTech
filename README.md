# विद्यामित्र — Marathi EdTech Platform (Pilot City: Solapur)

An AI-native learning platform for Marathi-medium students in Maharashtra. Students get an interactive tutor ("AI Guru / Mitra") that speaks Marathi, teachers get attendance and progress tools, parents get a weekly WhatsApp report, and the whole thing is built to run on nearly free infrastructure until it earns its keep.

## Documentation

All project documentation lives in the `docs/` folder:

| File | Purpose |
|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System design, tech stack rationale, data model, AI/safety design, security, compliance |
| [`DEPLOYMENT.md`](DEPLOYMENT.md) | Local setup → free-tier pilot hosting → scale-up, with a cost table |
| [`ANTIGRAVITY_PROMPT.md`](ANTIGRAVITY_PROMPT.md) | Copy-paste build prompt for Antigravity IDE / Claude Opus |
| [`docs/implementation_plan.md`](docs/implementation_plan.md) | Phase 2 implementation plan: AI Guru chat, syllabus browser, student features |
| [`docs/walkthrough.md`](docs/walkthrough.md) | Full walkthrough: what was built across all phases, verification results |
| [`docs/task.md`](docs/task.md) | Comprehensive task tracker: all phases with completion status |
| [`docs/LOCAL_SETUP.md`](docs/LOCAL_SETUP.md) | Step-by-step local development setup guide (Docker, Python, Node) |
| `architecture-diagram.mermaid` | Component diagram of the whole system |
| `ai-cost-optimization-flow.mermaid` | How a student question is answered without hitting the LLM every time |
| `docker-compose.yml` | One-command local environment (Postgres, Redis, backend, realtime gateway) |
| `.env.example` | Every environment variable the stack needs, with no real secrets |

## Roles and what they see

- **Student** — syllabus, assignments, tests, and "AI Guru/Mitra" (text + voice chat in Marathi, restricted to syllabus topics)
- **Teacher** — attendance, test completion, per-student progress/weakness, and a view of what students are asking the AI (for pedagogy and safety)
- **Parent** — one dashboard for multiple children, same progress/weakness view as teachers, weekly WhatsApp report
- **Admin** — syllabus upload/versioning (PDF), user profile management (mobile/email updates)
- **Super Admin** — master data, full AI chat audit access, AI spend dashboard, homepage/marketing content, hidden login URL
- **School Profile** — stubbed in the data model, intentionally not built until a school signs on

## Quick start (local, zero cost)

```bash
git clone <your-repo-url> edtech-platform && cd edtech-platform
cp .env.example .env          # fill in API keys as you get them; Anthropic key is the only one needed on day one
docker compose up -d postgres redis   # starts Postgres+pgvector, Redis
cd backend && python -m venv .venv && pip install -e ".[dev]"
alembic upgrade head          # creates all 22 tables
python -m app.scripts.seed_dev_users  # seeds 5 test users
python -m app.scripts.seed_syllabus   # seeds Maharashtra State Board syllabus (grades 5–10)
uvicorn app.main:app --reload  # backend at :8000
# In a new terminal:
cd realtime-gateway && npm install && npm run dev  # gateway at :4000
# In a new terminal:
cd frontend && npm install && npm run dev          # PWA at :5173
```

Dev OTP code: `123456` (works for all phone numbers in local mode, zero SMS cost).

See [`docs/LOCAL_SETUP.md`](docs/LOCAL_SETUP.md) for the full guide with troubleshooting.

## Status

- [x] Architecture, tech stack, and cost model defined
- [x] Local dev environment scaffolded (docker-compose)
- [x] **Phase 1 complete** — backend (FastAPI + 22 tables + auth + RBAC), realtime gateway (Socket.io), frontend (React PWA + 5 dashboard shells)
- [x] **Phase 2 complete** — AI Guru chat (cache-first flow + streaming), syllabus browser, functional student dashboard, progress service, safety fixes, seed data
- [x] **Phase 3 complete** — Teacher dashboard (attendance, student progress, AI usage oversight, assignments), Parent dashboard (children, progress, weekly reports, notification prefs), report generation service
- [ ] Infrastructure verification — Docker compose up, Alembic migration, pytest, RBAC end-to-end
- [ ] Phase 4 — Admin + Super Admin panels
- [ ] Phase 5 — Payments + WhatsApp reports
- [ ] Phase 6 — Security hardening + free-tier pilot deploy
- [ ] School Profile module (later, only once a school signs on)

