# Deployment & Hosting Plan

Three phases: local (your laptop, ₹0), free-tier pilot (Solapur pilot, near-₹0 infra), and small-scale (once real schools/parents depend on it). Figures below are estimates from mid-2026 pricing pages — always check the provider's current page before committing, since free tiers are the most-changed line item in cloud pricing.

## Phase 0 — Local development (your laptop)

Prerequisites: Docker Desktop, Node.js 20+, Python 3.12+, Git.

```bash
git clone <your-repo-url> edtech-platform && cd edtech-platform
cp .env.example .env
# Fill in ANTHROPIC_API_KEY at minimum. Leave PAYMENT_PROVIDER=offline_mock
# and WHATSAPP_* blank to test everything else without those accounts yet.
docker compose up --build
```

This brings up Postgres (with `pgvector`), Redis, the FastAPI backend, and the Node realtime gateway — all on your machine, fully offline except for actual Claude API calls. Run the frontend separately (`npm run dev` in `/frontend`) once Antigravity has scaffolded it.

**End-to-end local test checklist** before touching the cloud:
1. Mobile-OTP login flow for each of the five roles (use a fixed test OTP in dev mode — don't burn real SMS credits locally)
2. Student: ask AI Guru the same question twice — second time should hit cache (check logs for `cache_hit: true`)
3. Teacher: mark attendance, view a student's AI-topic summary
4. Parent: link two children to one account, view combined dashboard
5. Admin: upload a syllabus PDF, confirm it's parsed into chapters
6. Super Admin: check the AI-cost dashboard shows non-zero token spend from step 2
7. Payment: run a purchase through `offline_mock`, then switch to `razorpay_test` and repeat using Razorpay's test UPI ID `success@razorpay` (and `failure@razorpay` to confirm failure handling)
8. WhatsApp: point the webhook at a tunnel (e.g., `ngrok`) and confirm an inbound message reaches the Node gateway

## Phase 1 — Free-tier pilot hosting

| Service | Provider | Free-tier reality check |
|---|---|---|
| Frontend (React PWA) | Cloudflare Pages | Free, no card required; unlike Vercel's Hobby tier, Cloudflare's free tier isn't restricted to non-commercial use — worth re-confirming on their current ToS page before you start charging money, but it's the safer free default here |
| Realtime gateway + Backend | Render (Free web services) | 512MB RAM/instance, spins down after 15 min idle, ~30–60s cold start on the next request, 750 free instance-hours/month shared across your free services. Fine for a pilot demo; upgrade to Starter (~$7/mo per service) the moment a teacher or parent is relying on it not being asleep |
| Database | Neon (Free) | Permanent free tier, no card required: ~100 compute-hours/month and 0.5GB storage per project, `pgvector` supported natively — don't use Render's free Postgres for anything real, it auto-deletes around 30 days |
| Cache | Upstash Redis (Free) | 256MB, 500K commands/month, pay-per-request beyond that — realistically ₹0 at pilot volume |
| Object storage | Cloudflare R2 (Free) | 10GB storage, 1M write + 10M read ops/month, **zero egress fees ever** — this matters once avatar videos and audio start adding up |
| Domain | Any registrar | Optional at first (use the free subdomain from Cloudflare Pages/Render); budget ~₹700–900/year for a `.in` or `.com` when you want one |

Setup order: Neon project → Upstash database → R2 bucket → Render services (point `DATABASE_URL`/`REDIS_URL`/R2 credentials at them via environment variables) → Cloudflare Pages pointed at your frontend build.

### WhatsApp Cloud API setup
1. Create a Meta Business Account and WhatsApp Business Account (WABA), verify the business
2. Rather than raw Cloud API, sign up with an India-friendly BSP (AiSensy, Interakt, Gupshup, or WATI) — they handle template submission/approval and give you a dashboard; budget roughly ₹1,000–2,500/month for the platform fee
3. Submit your weekly-report message as a **Utility** template for approval (this category has the lowest per-message rate and matches what it actually is — a transactional update, not marketing)
4. Point the BSP's webhook at your Node gateway's public URL

### Payment gateway activation
1. Build and test entirely against Razorpay **Test Mode** (no KYC required) — generate test API keys from Settings → API Keys in test mode
2. When ready for real money: complete Razorpay KYC (PAN, bank account, business proof), generate live keys, and flip `PAYMENT_PROVIDER=razorpay_live`
3. Keep webhook signature verification on regardless of mode — don't trust unsigned callbacks

## Phase 2 — Small-scale (a few hundred real students)

Move off free-tier cold starts first (Render Starter, ~$7–14/month for 1–2 services) since that's the thing real users actually notice. Everything else can often stay on its current provider's paid usage-based tier rather than a wholesale migration — Neon, Upstash, and R2 all scale from their free tier into pay-as-you-go without a re-platform.

## Estimated monthly cost by phase

| Phase | Infra (hosting/DB/cache/storage) | WhatsApp BSP | LLM + voice (cache-optimized) | Total (rough) |
|---|---|---|---|---|
| 0 — Local | ₹0 | ₹0 | ₹0 (or a few rupees testing) | **₹0** |
| 1 — Pilot | ₹0 (free tiers) | ~₹1,000–1,500 | ~₹300–800 | **~₹1,500–2,500/month** |
| 2 — ~500 students | ~₹1,200 (Render Starter x2) | ~₹2,000–3,000 | ~₹2,000–4,000 | **~₹6,000–9,000/month** |

Razorpay's own fee (roughly 2% per successful transaction) isn't in this table since it scales with revenue, not a fixed cost. These are order-of-magnitude planning numbers, not quotes — verify current rates on each provider's pricing page before budgeting seriously.

## Monitoring (free tier)
- Uptime: UptimeRobot free plan (5-minute checks)
- Errors: Sentry free tier (5K errors/month is generous at pilot scale)
- AI spend: the Super Admin dashboard itself, since every call already logs its cost

## Pre-launch security checklist
- [ ] Secrets rotated from whatever was used in local dev
- [ ] Super Admin URL not linked anywhere public, TOTP enforced
- [ ] Database backups confirmed restorable (not just "scheduled")
- [ ] Rate limits verified under load, not just configured
- [ ] Razorpay webhook signature verification tested against a tampered payload
