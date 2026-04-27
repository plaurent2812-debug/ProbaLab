# ProbaLab Top 1 France Master Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the best French-market football + NHL probability and value betting application: reliable data, calibrated probabilities, transparent track record, premium UX, safe bankroll tooling, and production-grade operations.

**Product Positioning:** ProbaLab must not look like a tipster site. It must feel like a Bloomberg/TradingView-style decision cockpit for sports probabilities: calibrated models, explainable edges, historical proof, bankroll discipline, and fast daily execution.

**Architecture:** Keep production on `ProbaLab/api` and `ProbaLab/dashboard`. Freeze `/next-app/` until a dedicated migration plan exists. Build around API contracts, strict UTC, strict `fixture_id` typing, Supabase service-role backend access, RLS for user-owned tables, and tests as release gates.

**Tech Stack:** FastAPI, Supabase PostgreSQL/RLS, React 19, Vite, Tailwind 4, TanStack Query, Vitest/MSW, Pytest, Playwright, XGBoost, LightGBM, scikit-learn, Optuna, Gemini, Trigger.dev, Railway, GitHub Actions.

---

## North Star

ProbaLab wins the market if a user can answer these questions faster and with more trust than anywhere else:

- Which football and NHL bets have positive expected value today?
- Why does the model like this edge?
- How calibrated has this market been recently?
- What stake should I place for my bankroll and risk profile?
- What happened after the match, and did the model beat closing odds?
- Can I trust the track record without taking the app's word for it?

The product must be optimized for trust first, conversion second, and entertainment third.

## Non-Negotiable Principles

- No normal test suite may perform live network traffic.
- No user-facing prediction can omit timestamp, market, odds source, confidence, and risk context.
- No premium conversion copy may imply guaranteed profit.
- Every API powering V2 frontend must have a contract test.
- Every new Supabase user table must have RLS policies and policy tests.
- Every ML model shipped to production must have Brier, log loss, calibration, CLV, and data completeness tracking.
- Every production route must degrade gracefully with loading, empty, and error states.
- All times are UTC. No implicit timezone conversion.
- `fixture_id` stays strictly typed at every boundary.
- `next-app/` is not part of production until explicitly approved.

## Current Baseline

- Backend standard suite is green: `python -m pytest tests/ -m "not integration" -q`.
- Frontend Vitest suite is green: `VITE_API_URL=http://localhost:8000 npm run test:ci`.
- V2 home crash risks have been fixed: safe pick adapter, defensive safe card, root ErrorBoundary, cached `/api/performance/summary`.
- Live API-Football probes are opt-in integration tests.
- Provider accounts available: The Odds API paid plan at $30/month, API-Football PRO Plan.
- Remaining major known debt: global `npx tsc --noEmit` fails on legacy/admin/UI typing debt.
- Product foundation exists: V2 frontend, matches page, bankroll tracker, notification rules, public track record, safe pick, performance KPIs.

---

## Phase 0: Release Discipline And CI Gates

**Outcome:** The project can be trusted before any product acceleration. Green tests must mean something.

**Files:**
- Modify: `.github/workflows/ci.yml`
- Verify: `ProbaLab/pytest.ini`
- Verify: `ProbaLab/dashboard/package.json`
- Create: `docs/runbooks/quality-gates.md`

- [ ] **Step 0.1: Align backend CI with local verified command**

Set the backend command to:

```bash
cd ProbaLab && python -m pytest tests/ -m "not integration" --timeout=60 --cov=src --cov=api --cov-report=term-missing --cov-fail-under=21 -q
```

Expected: unit/integration boundary is explicit and no API-Football live probe runs.

- [ ] **Step 0.2: Align frontend CI with local verified command**

Set the frontend test job env:

```yaml
env:
  VITE_API_URL: http://localhost:8000
```

Run:

```bash
cd ProbaLab/dashboard && npm run test:ci
```

Expected: MSW handlers and hooks share the same API base.

- [ ] **Step 0.3: Add TypeScript strategy**

Do not block deployment on all legacy TypeScript debt immediately. Instead create two gates:

```bash
cd ProbaLab/dashboard && npx tsc --noEmit --project tsconfig.v2.json
cd ProbaLab/dashboard && npx tsc --noEmit
```

Expected:
- V2 production typecheck becomes mandatory first.
- Full legacy typecheck becomes a tracked cleanup milestone.

- [ ] **Step 0.4: Write quality gates runbook**

Create `docs/runbooks/quality-gates.md` with:

```markdown
# Quality Gates

Required before merge:
- Backend: `python -m pytest tests/ -m "not integration" -q`
- Frontend: `VITE_API_URL=http://localhost:8000 npm run test:ci`
- Whitespace: `git diff --check`
- Ruff on modified Python files
- No live API calls in standard tests

Optional/manual:
- API-Football probes: `RUN_LIVE_API_TESTS=1 ... -m integration`
- Playwright smoke after V2 deploy
```

**Done Criteria:**
- Backend CI, frontend CI, and local commands match.
- V2 typecheck has a clear mandatory path.
- Full TypeScript debt is visible but no longer blocks focused V2 work unpredictably.

---

## Phase 1: Production Readiness Foundation

**Outcome:** ProbaLab can be deployed, rolled back, and diagnosed like a serious production product.

**Files:**
- Verify: `Procfile`
- Verify: `ProbaLab/api/main.py`
- Verify: `ProbaLab/dashboard/src/app/v2/AppV2.tsx`
- Create: `docs/runbooks/prod-readiness.md`
- Create: `docs/runbooks/incident-response.md`

- [ ] **Step 1.1: Define required environment variables**

Document:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `API_FOOTBALL_KEY`
- `THE_ODDS_API_KEY`
- `GEMINI_API_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `RESEND_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `DISCORD_WEBHOOK_URL`
- `CRON_SECRET`
- `VITE_FRONTEND_V2`
- `VITE_API_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

- [ ] **Step 1.2: Define post-deploy smoke tests**

Document and run:

```bash
curl -fsS "$API_URL/health"
curl -fsS "$API_URL/api/performance/summary?window=30"
curl -fsS "$API_URL/api/matches?date=$(date -u +%F)"
curl -fsS "$APP_URL/"
```

Expected: all return successfully without unauthenticated admin access.

- [ ] **Step 1.3: Define rollback paths**

Document:
- Railway previous deployment rollback.
- `VITE_FRONTEND_V2=false` rollback.
- SQL migration rollback policy.
- Supabase RLS emergency verification.

- [ ] **Step 1.4: Add incident response runbook**

Include severity levels:
- P0: blank page, login broken, all predictions down, data corruption, security exposure.
- P1: one sport down, Stripe broken, notifications broken.
- P2: slow page, stale odds, copy issue, non-critical admin issue.

**Done Criteria:**
- Any deploy can be smoked in under 5 minutes.
- Any P0 has a documented rollback path.
- No one needs to guess env vars from code.

---

## Phase 2: Data Platform For Football And NHL

**Outcome:** The app's moat starts with data quality. If data is wrong or late, every model and UI layer is fake.

**Files:**
- Verify/modify: `ProbaLab/src/fetchers/`
- Verify/modify: `ProbaLab/src/models/`
- Verify/modify: `ProbaLab/api/routers/trigger.py`
- Create/modify: Supabase migrations for provider health and ingestion logs
- Test: `ProbaLab/tests/test_*ingestor*.py`

- [ ] **Step 2.1: Build provider health logging**

Create a table or extend existing logs with:
- provider name
- sport
- endpoint
- status code
- response row count
- latency ms
- quota remaining if available
- paid plan label (`the_odds_api_30_usd`, `api_football_pro`)
- recorded_at UTC

Expected: provider failures become visible before the UI is empty.

- [ ] **Step 2.2: Football ingestion completeness**

For each supported competition:
- Ligue 1
- Ligue 2
- Premier League
- La Liga
- Serie A
- Bundesliga
- Champions League
- Europa League

Verify daily:
- fixtures fetched
- odds fetched
- predictions generated
- results resolved after final score
- league IDs match expected IDs

- [ ] **Step 2.3: NHL ingestion completeness**

Verify daily:
- schedule fetched with `now -> now + 36h` window
- team name normalization works across providers
- odds availability is recorded explicitly
- fallback reason is visible when odds are missing
- final scores resolve picks correctly

- [ ] **Step 2.4: Add data completeness dashboard endpoint**

Create an admin endpoint:

```http
GET /api/admin/data-health
```

Return:
- fixtures today by sport
- predictions today by sport
- odds coverage by sport and market
- unresolved finished fixtures
- provider errors last 24h

- [ ] **Step 2.5: Add tests for provider failures**

Tests must prove:
- a provider returning HTTP 200 with zero data is not treated as success
- a provider timeout logs a failure
- NHL empty game day falls back to closest game day
- team name normalization handles punctuation and official renames

**Done Criteria:**
- Admin can tell if Football or NHL data is healthy in 30 seconds.
- The product never silently shows "no matches" when the actual issue is provider failure.
- Every provider integration has failure tests.

---

## Phase 3: Probability Engine And Calibration

**Outcome:** ProbaLab wins because probabilities are better calibrated, not because the UI is prettier.

**Dedicated execution plan:** `docs/superpowers/plans/2026-04-26-auto-training-performance-tracking.md` defines the complete MLOps loop: performance snapshots, retrain policy, candidate model training, promotion/rejection, rollback, Trigger.dev orchestration, and admin/public tracking.

**Files:**
- Verify/modify: `ProbaLab/src/models/ml_predictor.py`
- Verify/modify: `ProbaLab/src/prediction_blender.py`
- Verify/modify: `ProbaLab/src/monitoring/`
- Verify/modify: `ProbaLab/src/training/`
- Add/modify: `ProbaLab/tests/test_calibration_*.py`
- Add/modify: `ProbaLab/tests/test_model_health_*.py`

- [ ] **Step 3.1: Define model scorecard per sport**

Track for Football and NHL separately:
- Brier score
- log loss
- expected calibration error
- accuracy by market
- CLV mean
- CLV positive percentage
- ROI by market
- volume by market
- fallback rate
- data completeness

- [ ] **Step 3.2: Apply `model_health_log` migration**

Manual owner action still required:

```sql
create table if not exists model_health_log (
    id bigserial primary key,
    recorded_at timestamptz not null default now(),
    sport text not null check (sport in ('football','nhl')),
    brier_7d numeric,
    brier_30d numeric,
    log_loss_30d numeric,
    ece_30d numeric,
    clv_best_mean_30d numeric,
    drift_detected boolean default false,
    data_completeness_pct numeric,
    prediction_volume_today integer,
    alert_count integer default 0,
    ml_fallback_rate numeric,
    notes text
);
```

Expected: monitoring can persist daily health snapshots.

- [ ] **Step 3.3: Football model audit**

Validate:
- no data leakage
- time-based train/validation/test split
- calibration holdout separated from test set
- no rounding before final response
- league-level performance visible
- market-level performance visible

- [ ] **Step 3.4: NHL model audit**

Validate:
- moneyline model calibration
- player props fallback visibility
- provider coverage limits explicit
- NHL-specific time window correct
- team name normalization stable

- [ ] **Step 3.5: Add calibration monitoring job**

Daily job must:
- compute scorecard for last 7d, 30d, 90d
- insert `model_health_log`
- alert if Brier worsens beyond threshold
- alert if fallback rate exceeds threshold
- alert if data completeness drops

- [ ] **Step 3.6: Add model promotion rules**

No model can be promoted unless:
- Brier improves or stays within tolerance
- log loss improves or stays within tolerance
- calibration curve does not degrade materially
- minimum sample size is met
- recent holdout period is untouched during training

**Done Criteria:**
- A premium user can see model quality, not just predictions.
- Admin can detect model degradation in 24h.
- New models have promotion gates and rollback rules.

---

## Phase 4: Value Betting And Odds Intelligence

**Outcome:** The product becomes a decision engine: probability is only half the story; edge, odds source, market liquidity, and stake sizing make it useful.

**Files:**
- Verify/modify: `ProbaLab/api/routers/best_bets.py`
- Verify/modify: `ProbaLab/src/odds_comparator.py`
- Verify/modify: `ProbaLab/src/bankroll.py`
- Verify/modify: `ProbaLab/dashboard/src/pages/v2/MatchesV2.tsx`
- Verify/modify: `ProbaLab/dashboard/src/pages/v2/MatchDetailV2.tsx`
- Test: best bet, edge, EV, odds comparator, bankroll tests

- [ ] **Step 4.1: Standardize edge and EV definitions**

All code and UI must use:

```text
implied_prob = 1 / odds
edge = model_prob - implied_prob
ev = model_prob * odds - 1
```

Expected: no UI labels confuse EV and edge.

- [ ] **Step 4.2: Add closing line value tracking**

For each recommended pick:
- opening odds
- displayed odds
- closing odds
- CLV percentage
- bookmaker source
- timestamp UTC

- [ ] **Step 4.3: Build odds confidence indicators**

UI must show:
- real odds vs estimated odds
- last odds update UTC
- odds source
- stale odds warning
- low-liquidity warning if source is weak

- [ ] **Step 4.4: Bankroll risk tiers**

Add stake recommendations:
- Conservative: 0.25 Kelly cap
- Balanced: 0.5 Kelly cap
- Aggressive: 1.0 Kelly cap with hard max cap

Always display:
- stake amount
- bankroll percentage
- risk label
- warning for high variance markets

- [ ] **Step 4.5: Market coverage strategy**

Prioritize market quality over quantity:
- Football P0: 1X2, double chance, over/under 2.5, BTTS.
- Football P1: Asian handicap, team totals, correct score only if data supports it.
- NHL P0: moneyline, puck line, totals.
- NHL P1: player shots/goals/assists only if provider data is reliable.

Provider assumption: The Odds API paid $30/month and API-Football PRO Plan are available, so implementation should validate actual market coverage and quota from these plans before hiding or launching a market. Paid access improves reliability, but the app must still show provider coverage, stale odds, and missing market states honestly.

**Done Criteria:**
- Every recommended bet has probability, odds, edge, EV, stake, odds source, and update time.
- CLV becomes a first-class metric.
- The app refuses to overstate low-quality markets.

---

## Phase 5: User Experience And Premium Product

**Outcome:** The app feels like a high-end daily decision cockpit, not a dashboard full of tables.

**Files:**
- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.tsx`
- Modify: `ProbaLab/dashboard/src/pages/v2/MatchesV2.tsx`
- Modify: `ProbaLab/dashboard/src/pages/v2/MatchDetailV2.tsx`
- Modify: `ProbaLab/dashboard/src/pages/v2/PremiumV2.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/`
- Test: V2 page/component tests and accessibility tests

- [ ] **Step 5.1: Home page as trust cockpit**

Logged-in home must show:
- Safe pick of the day
- top value picks
- ROI 30d
- Brier 7d
- CLV 30d
- bankroll state
- next matches
- last update UTC

Visitor home must show:
- public track record
- example blurred premium insight
- proof-first pitch
- responsible gambling copy
- clear premium CTA

- [ ] **Step 5.2: Matches page as scanner**

The matches page must let users scan by:
- sport
- league
- market
- value only
- safe only
- high confidence
- kickoff window
- minimum edge
- odds freshness

Mobile must prioritize:
- team names
- market
- model probability
- edge
- best odds
- CTA to detail

- [ ] **Step 5.3: Match detail as explainability page**

Each match detail must show:
- model probabilities
- implied bookmaker probabilities
- edge by market
- top factors
- recent team form
- injuries/news if available
- H2H only as secondary context
- model uncertainty
- bankroll suggestion
- post-match resolution after final score

- [ ] **Step 5.4: Premium page as proof page**

Premium page must sell:
- transparent track record
- bankroll tools
- alerts
- value scanner
- detailed match analysis
- CLV proof

Avoid:
- "guaranteed profit"
- unrealistic win rates
- gambling hype

- [ ] **Step 5.5: Polish all loading/empty/error states**

Every V2 data block must have:
- loading skeleton
- empty state
- error state
- retry action when useful
- no raw technical error copy

**Done Criteria:**
- A new visitor understands the product in under 10 seconds.
- A paying user can find today's best decision in under 30 seconds.
- Mobile is not a downgraded desktop table.

---

## Phase 6: Personalization And Retention

**Outcome:** Users return daily because ProbaLab remembers their bankroll, preferences, leagues, markets, and alert rules.

**Files:**
- Verify/modify: `ProbaLab/api/routers/v2/notification_rules.py`
- Verify/modify: `ProbaLab/api/routers/v2/user_bankroll.py`
- Verify/modify: `ProbaLab/dashboard/src/pages/v2/AccountV2.tsx`
- Verify/modify: Supabase RLS migrations
- Test: notification rules, bankroll settings, RLS tests

- [ ] **Step 6.1: Preference profile**

Store:
- favorite sports
- favorite leagues
- preferred markets
- bankroll size
- risk profile
- alert channels
- timezone display preference while storing UTC

- [ ] **Step 6.2: Daily digest**

Generate daily user digest:
- top 3 value bets matching preferences
- safe pick
- bankroll exposure warning
- odds movement highlights
- watchlist matches

- [ ] **Step 6.3: Smart notifications**

Rules should support:
- edge threshold
- confidence threshold
- market
- league
- kickoff window
- odds movement
- bankroll drawdown
- CLV alert

- [ ] **Step 6.4: Post-match learning loop**

After resolution, show:
- result
- prediction probability
- closing odds
- CLV result
- ROI impact
- bankroll impact

**Done Criteria:**
- Users receive fewer, better alerts.
- Bankroll context affects recommendations.
- The app teaches users why picks won or lost without rewriting history.

---

## Phase 7: Security, Compliance, And Trust

**Outcome:** A betting-adjacent product must be safer and more transparent than competitors.

**Files:**
- Verify/modify: `ProbaLab/api/auth.py`
- Verify/modify: `ProbaLab/api/rate_limit.py`
- Verify/modify: `ProbaLab/api/schemas.py`
- Verify/modify: Supabase migrations and RLS policies
- Verify/modify: legal pages in dashboard
- Test: auth, RLS, rate limiting, schema strictness

- [ ] **Step 7.1: Endpoint auth audit**

Audit every:
- `POST`
- `PUT`
- `PATCH`
- `DELETE`
- `/admin/*`
- `/trigger/*`

For each endpoint record:
- auth dependency
- Pydantic schema
- rate limit
- user ownership check
- RLS interaction

- [ ] **Step 7.2: Strict schemas**

Every public write payload must use Pydantic with:

```python
model_config = ConfigDict(extra="forbid")
```

- [ ] **Step 7.3: RLS policy verification**

For each user table:
- users can read only their rows
- users can modify only their rows
- service role can run backend jobs
- anon cannot read private data

- [ ] **Step 7.4: Responsible gambling layer**

Add visible copy:
- probabilities are not guarantees
- stake suggestions are informational
- bankroll limits are user responsibility
- links to gambling help resources for France

- [ ] **Step 7.5: Stripe and entitlement hardening**

Verify:
- webhook signature
- idempotency
- subscription status sync
- entitlement cache invalidation
- downgrade behavior
- failed payment behavior

**Done Criteria:**
- No admin or trigger endpoint is public.
- No user-owned data bypasses RLS.
- Premium access is tied to verified subscription state, not frontend flags.

---

## Phase 8: Observability And Operations

**Outcome:** You know what is broken before users tell you.

**Files:**
- Modify: `ProbaLab/api/main.py`
- Modify: `ProbaLab/api/routers/*`
- Create: `docs/runbooks/observability.md`
- Add monitoring hooks where appropriate

- [ ] **Step 8.1: API health metrics**

Track:
- request count
- 4xx rate
- 5xx rate
- latency p50/p95/p99
- endpoint error rate
- provider error rate

- [ ] **Step 8.2: Product health metrics**

Track:
- daily active users
- visitor to signup conversion
- signup to premium conversion
- premium churn
- alert creation rate
- bankroll tracker usage
- match detail open rate

- [ ] **Step 8.3: Prediction health metrics**

Track:
- prediction volume by sport
- odds coverage
- stale odds rate
- Brier by sport/market
- CLV by sport/market
- ROI by sport/market
- fallback rate

- [ ] **Step 8.4: Alerting**

Alert on:
- `/health` down
- 5xx spike
- no fixtures for a sport with scheduled games
- no odds for supported markets
- model fallback rate spike
- Stripe webhook failures
- Trigger.dev job failures

**Done Criteria:**
- Admin can see app, data, model, and revenue health separately.
- Critical alerts go to Telegram/Discord.
- Debugging starts from dashboards, not guessing.

---

## Phase 9: Market Differentiation

**Outcome:** ProbaLab has a clear reason to exist against betting communities, bookmaker tools, and generic AI prediction sites.

- [ ] **Step 9.1: Public proof page**

Public track record must show:
- ROI 30d/90d
- CLV 30d/90d
- Brier score
- sample size
- market breakdown
- odds source mix
- last update UTC

- [ ] **Step 9.2: Calibration-first branding**

Core message:

```text
Des probabilités calibrées, pas des pronostics au feeling.
```

Secondary message:

```text
ProbaLab mesure ses modèles après chaque match : Brier, CLV, ROI, bankroll.
```

- [ ] **Step 9.3: France-first content**

Prioritize:
- Ligue 1 and Ligue 2 coverage quality
- French terminology
- French responsible gambling compliance
- premium copy in natural French
- euro bankroll formatting

- [ ] **Step 9.4: NHL niche domination**

NHL can be a differentiator in France if the product is sharper than generic football-only apps:
- explain NHL markets clearly
- expose provider coverage honestly
- prioritize moneyline/totals before fragile props
- add team normalization confidence
- show game start times clearly for late-night matches

**Done Criteria:**
- A user can explain why ProbaLab is different in one sentence.
- Public proof page is credible without login.
- NHL is treated as a serious vertical, not an afterthought.

---

## Phase 10: Launch Plan

**Outcome:** Ship in controlled waves, not as one risky mega-release.

- [ ] **Step 10.1: Internal beta**

Run for 7 days:
- all daily jobs
- all smoke tests
- manual betting slate review
- admin data health checks
- frontend error review

Exit criteria:
- no P0
- no repeated P1
- odds coverage known
- model health logs present

- [ ] **Step 10.2: Private beta**

Invite 10-30 users:
- football-first users
- NHL niche users
- bankroll-focused users

Collect:
- "Did you understand the edge?"
- "Did you trust the probability?"
- "Could you find today's best picks?"
- "What stopped you from subscribing?"

- [ ] **Step 10.3: Paid launch**

Enable:
- premium subscription
- public track record
- safe pick free acquisition loop
- email/Telegram notification capture
- landing page proof section

- [ ] **Step 10.4: Growth loop**

Weekly publishable assets:
- "Safe du jour" public
- top CLV movement recap
- Ligue 1 value watch
- NHL night slate watch
- monthly transparent performance report

**Done Criteria:**
- Launch is measured by trust and retention, not only traffic.
- Paid funnel works end to end.
- Public claims are backed by database metrics.

---

## 30-Day Execution Order

### Week 1: Make The Foundation Unbreakable

- [ ] Lock CI commands.
- [ ] Create V2-only typecheck gate.
- [ ] Write prod readiness runbook.
- [ ] Add V2 API contract tests.
- [ ] Fix highest-risk frontend error states.
- [ ] Apply `model_health_log` migration.

### Week 2: Data And Model Trust

- [ ] Add provider health logging.
- [ ] Add data health endpoint.
- [ ] Add daily model health job.
- [ ] Add Brier/log loss/ECE/CLV snapshots.
- [ ] Add admin model/data health screens.

### Week 3: Value Betting Product

- [ ] Standardize edge/EV everywhere.
- [ ] Add CLV tracking.
- [ ] Add odds freshness and source indicators.
- [ ] Add bankroll risk tiers.
- [ ] Improve match detail explainability.

### Week 4: Premium And Launch Readiness

- [ ] Polish home, matches, premium, account UX.
- [ ] Add public proof page.
- [ ] Harden Stripe entitlement.
- [ ] Run internal beta checklist.
- [ ] Prepare private beta onboarding.

---

## Top 1 France Scorecard

Track weekly:

- Probability quality: Brier 7d/30d by sport and market.
- Market sharpness: CLV mean and positive CLV percentage.
- Product trust: public track record freshness and sample size.
- User value: premium user daily return rate.
- Conversion: visitor to signup, signup to premium, premium retention.
- Reliability: 5xx rate, provider failures, stale odds rate.
- UX quality: blank page count, frontend error count, mobile task completion.
- Safety: RLS tests, admin endpoint auth, Stripe entitlement correctness.

## Final Definition Of Done

ProbaLab is "top 1 France ready" when:

- Backend suite is green.
- Frontend suite is green.
- V2 production typecheck is green.
- Full smoke checklist passes after deploy.
- Public track record updates automatically.
- Football and NHL data health is visible.
- Model health is logged daily.
- Every pick has probability, odds, edge, EV, CLV tracking, and bankroll context.
- Premium subscription and entitlement flow is verified.
- No user-facing core page can render a blank page.
- No standard test hits live APIs.
- The app can be rolled back in under 5 minutes.
