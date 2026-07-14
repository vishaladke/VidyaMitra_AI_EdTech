# Architecture — Marathi EdTech Platform

## 1. Vision

An AI-native EdTech platform for Marathi-medium students in Maharashtra, piloting in Solapur before expanding state-wide. The differentiator is the "AI Guru / Mitra" — a syllabus-restricted tutor that talks to students in Marathi (text and voice) — wrapped in dashboards for students, teachers, parents, and admins, with a cost architecture designed to run on near-zero infrastructure spend until revenue justifies more.

Content note: if the comedic "Gondhal Guruji" Marathi video pipeline (Claude-scripted, Sarvam Bulbul/ElevenLabs voice, HeyGen avatar) is meant to sit alongside this platform, that same voice/avatar pipeline can double as the source for AI Guru's short explainer clips and its voice persona — no need to build a second production pipeline for it.

## 2. Roles and permissions

| Role | Core capability | Data visibility |
|---|---|---|
| Student | Tutorials, assignments, tests, AI Guru chat/voice | Own data only |
| Teacher | Attendance, test tracking, class roster | All students assigned to them |
| Parent | Weekly report, progress/weakness/strength | Own linked children only (many-to-many: one parent, multiple kids) |
| Admin | Syllabus CRUD, user profile management | All users, no billing/AI-cost data |
| Super Admin | Master data, AI cost + full chat audit, homepage/ads, reporting | Everything |
| School (future) | Not built yet — stubbed in schema | N/A until a school signs a data-sharing agreement |

## 3. System architecture

See `architecture-diagram.mermaid` for the full component diagram. Summary of the moving parts:

- **React PWA** (installable on a phone home screen without an app-store release) is the single frontend for web and "mobile app." A Capacitor.js wrapper is a Phase 2 option if Play Store/App Store presence becomes worth the extra packaging — it reuses the same React code, so it's not a second codebase.
- **Node.js + Socket.io** is a thin realtime gateway sitting in front of the Python backend: it streams AI chat/voice turns and receives WhatsApp webhooks. This matches the "React + Node.js frontend, Python backend" split in the brief — Node isn't duplicating backend logic, it's handling the two things Python/FastAPI is comparatively clumsier at (long-lived socket connections, webhook fan-in).
- **Python FastAPI** is the core backend: auth/RBAC, all five role services, syllabus and test engine, and the weekly report generator. FastAPI's built-in OpenAPI/Swagger docs double as living API documentation with no extra work.
- **AI orchestration layer** is the cost-control heart of the system (detailed in §7).
- **PostgreSQL (Neon)** is the system of record, with the `pgvector` extension used for the semantic cache — this avoids running a separate vector database.
- **Redis (Upstash)** handles the exact-match Q&A cache, session/rate-limit state.
- **Cloudflare R2** stores syllabus PDFs, AI Guru avatar clips, and TTS audio — zero egress fees matter here since video/audio is bandwidth-heavy.

## 4. Tech stack decisions

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript + Tailwind | Matches the brief; Vite gives fast local iteration; Tailwind keeps a simple, elegant UI achievable without a design team |
| Mobile | PWA first, Capacitor wrapper later | One codebase; avoids maintaining native iOS/Android builds before there's revenue to justify it |
| Realtime gateway | Node.js + Express + Socket.io | Long-lived connections and webhook fan-in are Node's strength; keeps Python backend simple |
| Backend | Python 3.12 + FastAPI + SQLAlchemy (async) + Pydantic | Matches the brief's "Python + Python data modules"; async FastAPI performs well for I/O-bound AI-call-heavy workloads |
| Database | PostgreSQL via Neon | Permanent free tier, no card required, native `pgvector` support removes a separate vector DB |
| Cache | Redis via Upstash | Serverless pay-per-request — genuinely near-zero at pilot volume, no idle server cost |
| Object storage | Cloudflare R2 | 10GB free forever, zero egress fees — matters for video/audio/PDF delivery |
| LLM | Claude API — Haiku 4.5 default, Sonnet 4.6 for harder reasoning | Haiku 4.5 is Anthropic's current cheapest tier ($1/$5 per million input/output tokens) and is explicitly positioned for high-volume, latency-sensitive work — a good fit for routine student Q&A |
| Voice (Marathi) | Sarvam Bulbul v3 (TTS) + Saaras v3 (STT) | Already in use for the Gondhal Guruji pipeline; strong Marathi support; INR pricing with ₹1,000 free credit to start |
| Payments | Razorpay | Native test mode (sandbox keys, test UPI IDs, mock webhooks) needs no KYC to build against; India-first payment methods (UPI, cards, netbanking) |
| OTP/Auth | Firebase Phone Auth (default) or MSG91 (India-specific alternative) | Firebase handles rate-limiting/fraud detection out of the box; billed per SMS verification either way, so compare actual per-SMS cost once volume is known |
| Notifications | WhatsApp Cloud API via a BSP (AiSensy/Interakt/Gupshup/WATI) | Direct Cloud API access is possible but the webhook/template-review/verification overhead is real; a BSP earns its ~₹1,000–2,500/month fee early on |

## 5. Module specifications

### Student Dashboard
- Syllabus browser (subject → chapter → topic), assignments, tests with auto-grading where possible
- AI Guru/Mitra: text and voice chat, Marathi-first, scoped to the student's grade/subject/current syllabus
- Personal progress view (completion %, streaks)

### Teacher Dashboard
- Class roster, attendance marking, test-completion tracking
- Per-student drill-down: progress, strengths/weaknesses derived from test analytics
- AI usage oversight: topic-level view of what a student has been asking the AI (not raw transcripts by default — see §7 on why this framing matters for safety and trust)
- Assign tests/homework

### Parent Dashboard
- Multi-child selector (one parent account, many linked children)
- Same progress/weakness/strength view as teachers, plus the weekly WhatsApp report content mirrored in-app
- Notification preferences

### Admin Dashboard
- Syllabus CRUD, including PDF upload and versioning
- User management: Student/Teacher/Parent profile updates, mobile/email changes
- Class/section management, teacher-to-student assignment

### Super Admin Dashboard
- Master data (subjects, boards, grade levels)
- AI cost dashboard: tokens + ₹ spent, cache-hit rate, per-school/per-user breakdown
- Full AI chat audit log access, with logging/retention scoped to what's needed for safety oversight (avoid hoarding data beyond that — see §9)
- Homepage/marketing content CMS and ad-slot management (see the ad-placement note in §9 — this is a DPDP Act constraint, not just a design preference)
- Cross-feature reporting
- Login at a separate, unlisted URL (see §8)

### School Profile (deferred)
Stub the data model now (a `schools` table with a nullable FK from `classes`) so it's a additive migration later, but don't build the UI until a school actually signs a data-sharing agreement.

### Public homepage
About Us, Terms & Conditions, Refund Policy, low-cost pricing tiers, a Marathi-language feature walkthrough, and a CMS-managed "emerging skills in AI/data" content block. A "latest tech news" section is explicitly Phase 2.

## 6. Data model (core entities)

`users` (role enum) → `student_profiles` / `teacher_profiles` / `parent_profiles` (1:1 with users) → `parent_student_links` (many-to-many, since a parent can have multiple children and — less commonly — a student could have multiple guardians) → `schools` (nullable, future) → `classes`/`sections` → `subjects` → `syllabus_units` (chapter/topic tree, versioned, sourced from admin-uploaded PDFs) → `assignments` / `tests` / `test_attempts` / `questions` → `ai_conversations` / `ai_messages` (with a `topic_tag` column populated from a cheap classifier pass, which is what powers the teacher's "topics asked" view without exposing raw chat by default) → `attendance_records` → `payments` / `subscriptions` → `audit_logs` (all Super Admin and Admin actions) → `homepage_content` / `ad_slots`.

## 7. AI layer design

### Cost optimization (see `ai-cost-optimization-flow.mermaid`)
A student's question is checked, in order, against: (1) an exact-match Redis cache, (2) a `pgvector` semantic-similarity cache (catches paraphrased repeats — very common when many students ask about the same syllabus topic), (3) a pre-generated FAQ bank seeded *before launch* by batch-processing the syllabus's common questions, and only then (4) a live Claude API call. Two Anthropic-specific levers compound this: prompt caching (the system prompt and syllabus context are cached, cutting repeated-context input cost by roughly 90% on cache hits) and the Message Batches API (50% off) for generating that pre-launch FAQ bank in bulk. Every call — cached or not — logs its token cost to the Super Admin dashboard, so the cache-hit-rate ROI is visible, not assumed.

Model choice: Claude Haiku 4.5 ($1 input / $5 output per million tokens) as the default for routine Q&A; Claude Sonnet 4.6 ($3/$15) reserved for harder multi-step reasoning or generating the weekly parent-report narrative, where the extra quality is worth the modest extra cost at low volume.

### Marathi voice pipeline
Sarvam Saaras v3 (speech-to-text) → Claude (reasoning, text) → Sarvam Bulbul v3 (text-to-speech). This hybrid split — Indic-language-specialist models for voice, a frontier model for reasoning — is the pattern Sarvam itself recommends, and it's also what the Gondhal Guruji pipeline already uses, so there's shared tooling rather than a second stack to maintain. Build voice as push-to-talk (record → transcribe → respond → speak) rather than full-duplex real-time streaming for v1 — it's dramatically simpler and cheaper, and real-time streaming is a reasonable Phase 2 upgrade once there's usage data to justify it.

### Safety guardrails for AI Guru — this is not optional
Every student using this is a minor, so the design has to hold up on its own, not just rely on good intentions:
- **Hard topic restriction.** The system prompt scopes AI Guru strictly to the student's current syllabus/subject. Off-topic or inappropriate requests get a kind redirect back to studies, not a workaround.
- **No companion framing.** AI Guru is a study buddy, explicitly not a confidant or a secret-keeper. It should never encourage a student to keep a conversation private from a parent or teacher.
- **Full logging, teacher/parent visibility by design.** Every conversation is logged, and the *existence* of that logging is transparent to students and parents — this is a feature (it's what powers the teacher's "how does this student question things" view), not surveillance bolted on after the fact.
- **Escalation path for distress signals.** If a student's message suggests self-harm, abuse, or serious distress, the system should flag it for human (teacher/counselor) review rather than have the AI attempt to handle it alone. Route to a fixed, non-AI-generated safety message plus a human-review queue.
- **Data minimization.** Collect what's needed for tutoring and progress-tracking; avoid incidental collection (e.g., don't log device-level behavioral data beyond what the product needs).

## 8. Security architecture

- HTTPS everywhere; JWT access tokens (short-lived) + refresh tokens
- RBAC enforced at the API layer for all five roles, not just hidden in the UI
- Rate limiting per-IP and per-user (Redis-backed)
- Input validation via Pydantic on every endpoint
- Secrets in environment variables / a secrets manager — never committed to the repo
- Super Admin login on a separate, unlisted path (not linked from any public nav), with its own rate-limited lockout and a mandatory second factor (TOTP) regardless of the OTP flow everyone else uses
- Audit log for every Admin/Super Admin action
- Automated dependency scanning (`pip-audit`, `npm audit`) in CI
- Database backups tested, not just scheduled

## 9. Compliance notes (India — DPDP Act, 2023)

This isn't legal advice — verify specifics with a lawyer before launch — but the shape of the obligation is worth designing around from day one rather than retrofitting later:

- The DPDP Rules, 2025 (notified November 2025, phased compliance through May 2027) set a **uniform under-18 threshold** and require **verifiable parental consent** before processing a minor's personal data. Since every student on this platform is a minor, the signup/consent flow needs a parent-verification step baked in from the first release, not added later.
- The Act **prohibits behavioural tracking and targeted advertising directed at children**. This directly affects the Super Admin's "marketing ad" feature: ads should not be shown inside the student's active learning surfaces, and definitely not targeted using the student's own activity data. Keep monetized ad placements (if any) to parent/teacher/admin-facing screens, and prefer non-behavioral, contextual placements even there.
- Breach notification and data-fiduciary obligations apply regardless of company size — reasonable security safeguards (§8) aren't just best practice here, they're the compliance baseline.
- Being ahead of this is also a trust/marketing asset: parents are the actual buyers, and "we designed for child-data protection from day one" is a legitimate differentiator in a market where most competitors haven't started.

## 10. Payments architecture

A `PaymentProvider` interface with three implementations, selected by an environment variable:
- `offline_mock` — pure local, zero network calls, for fully offline dev
- `razorpay_test` — Razorpay's real sandbox (test API keys, test UPI IDs like `success@razorpay` / `failure@razorpay`, simulated webhooks) — no KYC needed to build and test the entire purchase flow end-to-end
- `razorpay_live` — production, activated once KYC/business registration is complete

This means "build a local dummy for local testing" and "integrate a real Indian payment system" are the same code path with one config change, not two separate implementations to maintain.

## 11. Notifications architecture

WhatsApp is the primary channel (per the brief), abstracted behind a `NotificationChannel` interface so email/SMS/native-push can be added later without touching call sites. The weekly parent report is a **Utility**-category template message (transactional, not promotional) — Meta's per-message rates for Utility templates in India are low (well under ₹1/message), but sending it at all requires a Meta-approved message template and, practically, a BSP subscription (AiSensy/Interakt/Gupshup/WATI, roughly ₹1,000–2,500/month) since raw Cloud API access means building webhook handling, template management, and business verification yourself. Any reply-driven conversation (a parent messaging back) falls into a free 24-hour service window — no extra charge for replies inside it.

## 12. Non-functional targets (pilot scale)

Design for hundreds, not tens of thousands, of concurrent users at first — that's what keeps the free-tier hosting story true. Revisit these targets once Solapur pilot numbers are real:
- API p95 latency target: under 500ms for non-AI endpoints, under 4s for a full AI-Guru text turn (cache hit should be near-instant)
- Availability: best-effort at pilot stage (free-tier cold starts are an accepted tradeoff — see `DEPLOYMENT.md`); move to always-on instances once a school depends on uptime
- Data retention: define explicit retention windows per data type (test results long-term, raw AI chat logs shorter, per §9)

## 13. Roadmap (explicitly deferred)

- School Profile module (data model stubbed now, UI built once a school signs on)
- Homepage "latest tech news" section
- Full-duplex real-time voice (replacing push-to-talk)
- Native app store presence via Capacitor
