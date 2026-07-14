# Build prompt for Antigravity IDE

**A note on the model first:** Antigravity (Google's agentic IDE) supports Claude alongside Gemini and GPT-OSS — Claude Opus 4.6 is a real, current option in its model picker, so no correction needed there. If a newer Opus (4.7 or 4.8) shows up in your picker by the time you set this up, pick that instead — same price per token, more capability. Either way, use an Opus-tier model for this build: it involves multi-file architectural reasoning across five role-based dashboards, which is exactly where Opus earns its premium over Sonnet or Haiku.

Set Antigravity to **Agent-assisted** mode (not full autopilot) for this project — you stay in the loop, the agent handles the safe automation. Put `ARCHITECTURE.md` and `DEPLOYMENT.md` from this pack into the repo's `/docs` folder before starting; the prompt below assumes the agent can read them.

---

## Copy everything below into Antigravity

You are acting as a senior full-stack engineer building an EdTech platform for Marathi-medium students in Maharashtra (pilot city: Solapur), end to end, inside this repository.

**Before writing any code:** read `docs/ARCHITECTURE.md` and `docs/DEPLOYMENT.md` in full. They contain the system design, tech stack, data model, AI safety requirements, and hosting plan. Treat them as the spec. If anything here conflicts with them, the docs win — flag the conflict to me rather than silently picking one.

### Non-negotiable constraints

- **Stack:** React + Vite + TypeScript + Tailwind (frontend, PWA-installable) · Node.js + Express + Socket.io (realtime gateway: AI chat streaming, WhatsApp webhooks) · Python 3.12 + FastAPI + SQLAlchemy async + Pydantic (core backend) · PostgreSQL with `pgvector` (Neon-compatible) · Redis (Upstash-compatible) · Cloudflare R2 (S3-compatible object storage)
- **Cost discipline is a hard requirement, not a preference.** Every AI Guru query must go through the cache-first flow in `docs/ARCHITECTURE.md` §7 (exact-match Redis → semantic pgvector → pre-generated FAQ bank → live Claude call) before ever calling the LLM. Default model is Claude Haiku 4.5; do not default to a more expensive model without a specific reason.
- **Child safety is a hard requirement, not a preference.** Every AI Guru response path must: stay scoped to the student's syllabus/subject via the system prompt, log conversations for teacher/parent visibility by design, never encourage secrecy from a parent or teacher, and route anything resembling a distress signal to a fixed safety message plus a human-review flag rather than letting the model freelance a response.
- **RBAC for five roles** (Student, Teacher, Parent, Admin, Super Admin) enforced at the API layer, not just hidden in the UI.
- **Super Admin lives at an unlisted path**, isn't linked from any public navigation, and requires a second factor beyond the standard OTP flow.
- **Payments** go through a `PaymentProvider` interface with `offline_mock` and `razorpay_test`/`razorpay_live` implementations — build and test against the mock and Razorpay's real test mode; never hardcode against live keys during development.

### Working process

1. Propose the full file/folder scaffold and the initial database schema (as a migration, not just a diagram) and show it to me before generating application code.
2. Build in phases, and pause for my confirmation between phases rather than running ahead:
   - **Phase 1:** repo scaffold, Docker Compose wiring, mobile-OTP auth, empty role-based dashboard shells with routing/RBAC working end to end
   - **Phase 2:** Student dashboard — syllabus browser, assignments/tests, AI Guru chat (text first, cache-first flow wired even if the cache is trivially empty at first) — then voice (push-to-talk, Sarvam Saaras/Bulbul)
   - **Phase 3:** Teacher + Parent dashboards, including the weekly-report generation job
   - **Phase 4:** Admin + Super Admin, including the AI-cost dashboard reading real logged token spend
   - **Phase 5:** Payments (mock → Razorpay test) and WhatsApp integration (mock the BSP webhook locally before wiring a real one)
   - **Phase 6:** security hardening pass against the checklist in `docs/DEPLOYMENT.md`, then prepare the free-tier deploy configs
3. Write tests for the paths where a bug is expensive to discover late: auth/RBAC boundary checks, the cache-hit/cache-miss decision logic, and payment webhook signature verification.
4. Keep services independently runnable — I need to be able to `docker compose up` locally and test every role end to end without live API keys for anything except Claude (mock the rest).
5. If a requirement is ambiguous, make a reasonable call and tell me what you assumed rather than blocking — but flag it, don't bury it.

Start with step 1: propose the scaffold and schema.
