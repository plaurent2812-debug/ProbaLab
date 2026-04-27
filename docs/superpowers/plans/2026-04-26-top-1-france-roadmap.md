# ProbaLab Top 1 France Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn ProbaLab from a stabilized production app into a premium, trustworthy, conversion-ready sports prediction product for the French market.

**Architecture:** Keep the production frontend on `ProbaLab/dashboard` (React 19 + Vite) and the production backend on `ProbaLab/api` (FastAPI). Treat `/next-app/` as a frozen local sandbox until there is an explicit migration plan; do not mix it into production work.

**Tech Stack:** FastAPI, Supabase PostgreSQL/RLS, React 19, Vite, Tailwind 4, TanStack Query, Vitest/MSW, Pytest, XGBoost/LightGBM, Gemini, Railway, GitHub Actions.

---

## Current Baseline

- Backend standard suite is green: `python -m pytest tests/ -m "not integration" -q` -> 659 passed, 1 skipped, 186 deselected, 2 xfailed.
- Frontend full suite is green: `VITE_API_URL=http://localhost:8000 npm run test:ci` -> 744 passed.
- V2 blank page risks are fixed: safe pick adapter, defensive safe card rendering, root ErrorBoundary, cached `/api/performance/summary`.
- Live API-Football probes are now opt-in integration tests through `RUN_LIVE_API_TESTS=1`.
- Provider accounts available: The Odds API paid plan at $30/month, API-Football PRO Plan.
- `next-app/` remains out of production scope until a dedicated migration decision.

## Execution Order

### Task 1: Lock CI Quality Gates

**Files:**
- Modify: `.github/workflows/ci.yml`
- Verify: `ProbaLab/pytest.ini`
- Verify: `ProbaLab/dashboard/package.json`

- [ ] **Step 1: Make CI run the same backend command used locally**

Ensure the backend non-integration command is:

```bash
cd ProbaLab && python -m pytest tests/ -m "not integration" -q
```

Expected: no live API-Football probes run in normal CI.

- [ ] **Step 2: Make CI run the same frontend command used locally**

Ensure the frontend command injects the API base URL:

```bash
cd ProbaLab/dashboard && VITE_API_URL=http://localhost:8000 npm run test:ci
```

Expected: MSW tests use the same base URL as the hooks.

- [ ] **Step 3: Add a CI comment explaining live probes**

Document that API-Football live probes are only for manual checks:

```bash
RUN_LIVE_API_TESTS=1 python -m pytest tests/test_api_cs.py tests/test_api_cs2.py tests/test_api_cs_l1.py tests/test_cleansheets.py tests/test_cs_fields.py -m integration -q
```

- [ ] **Step 4: Verify full local gates**

Run:

```bash
cd ProbaLab && python -m pytest tests/ -m "not integration" -q
cd ProbaLab/dashboard && VITE_API_URL=http://localhost:8000 npm run test:ci
```

Expected: both commands pass.

### Task 2: Add Product Trust Layer

**Files:**
- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/home/*.tsx`
- Test: `ProbaLab/dashboard/src/pages/v2/HomeV2.test.tsx`

- [ ] **Step 1: Write a failing test for proof-first dashboard copy**

Add assertions that the logged-in home shows transparent metrics: ROI window, Brier/calibration, bankroll, and last update UTC.

- [ ] **Step 2: Implement the trust block**

Use existing `usePerformanceSummary` data. Copy must avoid guarantees and gambling hype; prefer proof language:

```text
Modèle suivi en continu
ROI 30J, précision, Brier 7J et bankroll sont recalculés automatiquement.
```

- [ ] **Step 3: Verify accessibility**

Run:

```bash
cd ProbaLab/dashboard && VITE_API_URL=http://localhost:8000 npm run test -- HomeV2 --run
```

Expected: Home tests pass and no new axe issue appears.

### Task 3: Strengthen API Contracts

**Files:**
- Add/modify: `ProbaLab/tests/test_api/test_v2_contracts.py`
- Verify: `ProbaLab/api/routers/v2/matches_v2.py`
- Verify: `ProbaLab/api/routers/v2/safe_pick.py`
- Verify: `ProbaLab/api/routers/performance.py`

- [ ] **Step 1: Add contract tests for V2 home dependencies**

Cover:
- `GET /api/matches`
- `GET /api/safe-pick`
- `GET /api/performance/summary`

- [ ] **Step 2: Assert frontend-critical keys**

Each test must assert exact top-level shape and snake_case/camelCase boundary:

```python
assert set(body) == {"date", "total", "groups"}
assert set(body["groups"][0]) == {"league_id", "league_name", "matches"}
```

- [ ] **Step 3: Run targeted contracts**

Run:

```bash
cd ProbaLab && python -m pytest tests/test_api/test_v2_contracts.py -q
```

Expected: all contract tests pass without network.

### Task 4: Production Readiness Pass

**Files:**
- Verify: `Procfile`
- Verify: `.github/workflows/ci.yml`
- Verify: `ProbaLab/api/main.py`
- Verify: `ProbaLab/dashboard/src/app/v2/AppV2.tsx`
- Create: `docs/runbooks/prod-readiness.md`

- [ ] **Step 1: Document required env vars**

Include Supabase, Stripe, Gemini, Resend, Telegram, Discord, Railway, and `CRON_SECRET`.

- [ ] **Step 2: Document rollback**

Include frontend V2 flag rollback, Railway deploy rollback, and migration rollback policy.

- [ ] **Step 3: Document smoke tests**

Minimum smoke tests:

```bash
curl -fsS "$API_URL/health"
curl -fsS "$API_URL/api/performance/summary?window=30"
curl -fsS "$API_URL/api/matches?date=$(date -u +%F)"
```

### Task 5: Premium UX Polish

**Files:**
- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.tsx`
- Modify: `ProbaLab/dashboard/src/pages/v2/MatchesV2.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/system/*.tsx`
- Test: related Vitest component/page tests

- [ ] **Step 1: Add empty/loading/error polish to top V2 pages**

Every data card must have:
- loading skeleton
- empty state
- retry affordance where useful
- no raw technical error in user-facing copy

- [ ] **Step 2: Add premium microcopy**

Use French market language:
- "Value détectée"
- "Confiance modèle"
- "Risque bankroll"
- "Dernière mise à jour UTC"

- [ ] **Step 3: Verify full frontend**

Run:

```bash
cd ProbaLab/dashboard && VITE_API_URL=http://localhost:8000 npm run test:ci
```

Expected: 744+ tests pass.

## Done Criteria

- Backend non-integration suite stays green.
- Frontend Vitest suite stays green.
- V2 home never renders a blank page on bad/missing safe pick data.
- No normal test performs live network traffic.
- `next-app/` remains frozen unless a dedicated migration plan is approved.
- Product copy emphasizes proof, discipline, calibration, and bankroll safety.
