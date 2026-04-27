# Sport Intelligence Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the V2 frontend from a trading/value-betting visual language to a premium "analyses et probabilités sportives" experience that can support paid subscription conversion.

**Architecture:** Keep the current V2 component structure and avoid new routes. Rework wording, hierarchy, and visual accents in the connected home and match detail screens, with tests pinning the new product language. Preserve data contracts and existing hooks; this is a UX/UI pass, not a backend change.

**Tech Stack:** React 19, Vite, TypeScript, Tailwind CSS utility classes, Vitest, Testing Library, MSW.

---

## File Structure

- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.tsx`
  - Replace trading hero wording with "Analyses et probabilités sportives".
  - Replace "Market pulse" with "Résumé de journée".
  - Use blue/cyan sport intelligence accent instead of green trading accent.

- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.test.tsx`
  - Add tests for the new connected-home product language.
  - Assert removed trading/value-first language is absent.

- Modify: `ProbaLab/dashboard/src/components/v2/home/SafeOfTheDayCard.tsx`
  - Reframe the Safe card as "Prono recommandé".
  - Replace bankroll wording with "Niveau de risque" and "Confiance".

- Modify: `ProbaLab/dashboard/src/components/v2/home/SafeOfTheDayCard.test.tsx`
  - Update assertions for the new label and risk wording.

- Modify: `ProbaLab/dashboard/src/components/v2/home/ValueBetsTeaser.tsx`
  - Keep file name for a small first pass, but change user-facing title to "Opportunités du jour" or "Pronos recommandés".
  - Hide advanced value/Kelly language at first level.

- Modify: `ProbaLab/dashboard/src/pages/v2/MatchDetailV2.tsx`
  - Rename the in-file decision panel concept from `MatchDecisionCockpit` to `MatchReadingPanel`.
  - Replace "Decision cockpit" with "Lecture du match".
  - Reframe fair odds/value metrics as model probability and recommendation context.

- Modify: `ProbaLab/dashboard/src/pages/v2/MatchDetailV2.test.tsx`
  - Replace Cockpit Trading test with Sport Intelligence hierarchy test.
  - Assert old terms are absent.

- Modify: `ProbaLab/dashboard/src/components/v2/match-detail/RecoCard.tsx`
  - Reframe "Recommandation modèle" as "Prono recommandé".
  - Use primary blue/cyan accents rather than value/trading green as the default.

- Modify: `ProbaLab/dashboard/src/components/v2/match-detail/RecoCard.test.tsx`
  - Update label/style contract tests.

- Modify: `ProbaLab/dashboard/src/components/v2/match-detail/ValueBetsList.tsx`
  - Rename visible heading to "Opportunités avancées" so value bets are advanced detail, not product identity.

- Modify: `ProbaLab/tasks/lessons.md`
  - Add a lesson after implementation if the final wording/UX rule is stable.

---

## Task 1: Connected Home Repositioning

**Files:**
- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.test.tsx`
- Modify: `ProbaLab/dashboard/src/pages/v2/HomeV2.tsx`

- [ ] **Step 1: Add failing connected-home wording test**

Add a test in the connected/premium describe block:

```tsx
it('frames the connected home as sport analysis and probabilities', async () => {
  mockUser({ role: 'premium', isVisitor: false });
  renderHome();
  await screen.findByTestId('home-v2');

  expect(screen.getByRole('heading', { name: /analyses et probabilités sportives/i })).toBeInTheDocument();
  expect(screen.getByText(/résumé de journée/i)).toBeInTheDocument();
  expect(screen.getByText(/confiance modèle/i)).toBeInTheDocument();
  expect(screen.queryByText(/trading desk/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/cockpit du jour/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/market pulse/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- HomeV2 --run
```

Expected: fails because the current UI still contains `ProbaLab trading desk`, `Cockpit du jour`, and `Market pulse`.

- [ ] **Step 3: Update `HomeV2.tsx` hero and summary wording**

Replace:

```tsx
ProbaLab trading desk
Cockpit du jour
Signaux value, bankroll et calibration au même endroit pour décider sans bruit.
Market pulse
Statut risque
```

With:

```tsx
Centre d'analyse ProbaLab
Analyses et probabilités sportives
Les matchs du jour, les probabilités clés et les signaux du modèle pour décider plus vite.
Résumé de journée
Confiance modèle
```

Change the hero tags from:

```tsx
['Edge positif', 'Kelly prudent', 'Brier surveillé']
```

To:

```tsx
['Probabilités 1X2', 'Scénarios modèles', 'Pronos recommandés']
```

- [ ] **Step 4: Use sport intelligence accent**

In the connected hero, change green-heavy styles to blue/cyan:

```tsx
border: '1px solid rgba(96,165,250,0.24)',
background:
  'radial-gradient(circle at 12% 0%, rgba(96,165,250,0.18), transparent 34%), linear-gradient(135deg, rgba(7,17,31,0.98), rgba(15,23,42,0.92))',
```

Keep `var(--primary)` if global tokens will be changed later; otherwise use inline blue for this first pass.

- [ ] **Step 5: Run home tests**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- HomeV2 --run
```

Expected: all `HomeV2` tests pass.

---

## Task 2: Home Cards and Opportunities Rewording

**Files:**
- Modify: `ProbaLab/dashboard/src/components/v2/home/SafeOfTheDayCard.test.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/home/SafeOfTheDayCard.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/home/ValueBetsTeaser.tsx`

- [ ] **Step 1: Update Safe card test**

Replace the old label assertion with:

```tsx
expect(screen.getByText(/PRONO · RECOMMANDÉ/i)).toBeInTheDocument();
expect(screen.getByText(/Niveau de risque/i)).toBeInTheDocument();
expect(screen.getByText(/Confiance/i)).toBeInTheDocument();
expect(screen.queryByText(/Risque bankroll/i)).not.toBeInTheDocument();
```

- [ ] **Step 2: Run the failing Safe card test**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- SafeOfTheDayCard --run
```

Expected: fails on the new label/risk wording.

- [ ] **Step 3: Update `SafeOfTheDayCard.tsx` visible wording**

Change:

```tsx
SAFE · TICKET CONTRÔLÉ
Risque bankroll
Mode
```

To:

```tsx
PRONO · RECOMMANDÉ
Niveau de risque
Confiance
```

For the second mini stat value, display:

```tsx
{pct}%
```

Instead of:

```tsx
Safe
```

- [ ] **Step 4: Update `ValueBetsTeaser.tsx` heading**

Change:

```tsx
Value desk
```

To:

```tsx
Opportunités du jour
```

Change the small footer from bookmaker-first:

```tsx
{items[0]!.topValueBet!.bestBook} offre la meilleure cote.
```

To analysis-first:

```tsx
Sélections issues des probabilités et signaux du modèle.
```

Keep the underlying `topValueBet` data for now; only the first-level product language changes.

- [ ] **Step 5: Run targeted home component tests**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- SafeOfTheDayCard ValueBetsTeaser HomeV2 --run
```

Expected: all targeted tests pass.

---

## Task 3: Match Detail Reading Panel

**Files:**
- Modify: `ProbaLab/dashboard/src/pages/v2/MatchDetailV2.test.tsx`
- Modify: `ProbaLab/dashboard/src/pages/v2/MatchDetailV2.tsx`

- [ ] **Step 1: Replace the Cockpit test**

Replace the existing test named `frames the match as a Cockpit Trading decision desk` with:

```tsx
it('frames the match detail as sport analysis and probabilities', async () => {
  renderAt(<MatchDetailV2 />);
  await screen.findByTestId('match-detail-v2');

  expect(screen.getByRole('heading', { name: /lecture du match/i })).toBeInTheDocument();
  expect(screen.getByText(/scénario probable/i)).toBeInTheDocument();
  expect(screen.getByText(/confiance modèle/i)).toBeInTheDocument();
  expect(screen.getByText(/cote juste modèle/i)).toBeInTheDocument();
  expect(screen.queryByText(/decision cockpit/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/ticket contrôlé/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/risque bankroll/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run the failing match detail test**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- MatchDetailV2 --run
```

Expected: fails because `Decision cockpit`, `Ticket contrôlé`, and `Risque bankroll` still exist.

- [ ] **Step 3: Rename in-file panel symbols**

In `MatchDetailV2.tsx`, rename:

```tsx
function MatchDecisionCockpit(...)
```

To:

```tsx
function MatchReadingPanel(...)
```

Update both mobile and desktop usages:

```tsx
<MatchReadingPanel
  recommendation={d.recommendation}
  recommendedMarket={recommendedMarket}
  probs={d.probs_1x2}
  bookOdds={bookOdds}
  homeName={d.header.home.name}
  awayName={d.header.away.name}
/>
```

- [ ] **Step 4: Replace visible panel wording**

Change:

```tsx
Ticket contrôlé
Decision cockpit
Le pari n'est validé que si le prix bookmaker reste supérieur au fair odds modèle.
Risque bankroll
Kelly conseillé
Fair odds
Edge modèle
```

To:

```tsx
Analyse du match
Lecture du match
Les probabilités du modèle résument le scénario le plus probable et les points de décision.
Niveau de risque
Confiance modèle
Cote juste modèle
Signal modèle
```

Compute confidence from the recommendation when present:

```tsx
const confidencePct = recommendation ? fmtPct(recommendation.confidence) : '—';
```

Use it in the metric:

```tsx
<DecisionMetric label="Confiance modèle" value={confidencePct} />
```

- [ ] **Step 5: Add a scenario line**

Inside the panel, before the metrics grid, add:

```tsx
<div
  className="mt-4 rounded-xl p-3 text-sm"
  style={{ border: '1px solid var(--border)', background: 'rgba(255,255,255,0.03)', color: 'var(--text)' }}
>
  <span className="block text-[11px] font-semibold uppercase tracking-[0.12em]" style={{ color: 'var(--text-muted)' }}>
    Scénario probable
  </span>
  <strong className="mt-1 block">
    {homeName} favori selon le modèle, nul à surveiller.
  </strong>
</div>
```

This is a first-pass static sentence built from the current available 1X2 data. A later backend pass can provide richer model-generated scenarios.

- [ ] **Step 6: Run match detail tests**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- MatchDetailV2 --run
```

Expected: all `MatchDetailV2` tests pass.

---

## Task 4: Recommendation and Advanced Opportunities Cards

**Files:**
- Modify: `ProbaLab/dashboard/src/components/v2/match-detail/RecoCard.test.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/match-detail/RecoCard.tsx`
- Modify: `ProbaLab/dashboard/src/components/v2/match-detail/ValueBetsList.tsx`

- [ ] **Step 1: Update RecoCard test**

Replace:

```tsx
expect(screen.getByText(/recommandation modèle/i)).toBeInTheDocument();
```

With:

```tsx
expect(screen.getByText(/prono recommandé/i)).toBeInTheDocument();
```

- [ ] **Step 2: Run failing RecoCard test**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- RecoCard --run
```

Expected: fails until the visible label is changed.

- [ ] **Step 3: Update `RecoCard.tsx` wording and accent**

Change:

```tsx
Recommandation modèle
```

To:

```tsx
Prono recommandé
```

Use blue primary for the badge/odds by default and keep green only for positive edge values if needed:

```tsx
style={{ color: 'var(--primary)' }}
```

- [ ] **Step 4: Update `ValueBetsList.tsx` heading**

Change:

```tsx
Value bets
```

To:

```tsx
Opportunités avancées
```

Keep lock messages unchanged for now, unless tests already assert the heading.

- [ ] **Step 5: Run targeted component tests**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci -- RecoCard ValueBetsList MatchDetailV2 --run
```

Expected: all targeted tests pass.

---

## Task 5: Lessons and Verification

**Files:**
- Modify: `ProbaLab/tasks/lessons.md`

- [ ] **Step 1: Add a lesson**

Append:

```md
| 2026-04-27 | Le wording premium trop orienté trading/value donnait une identité de tipster financier alors que le positionnement validé est analyses et probabilités sportives | Le premier niveau UX doit vendre la compréhension du match : probabilités, confiance modèle, scénario probable et explication IA ; les notions value/Kelly/bankroll restent en détails avancés |
```

- [ ] **Step 2: Run full frontend tests**

Run:

```bash
cd "ProbaLab/dashboard" && VITE_API_URL=http://localhost:8000 npm run test:ci
```

Expected:

```text
Test Files  103 passed
Tests       746 passed
```

The exact count may increase if new tests are added.

- [ ] **Step 3: Run lint**

Run:

```bash
cd "ProbaLab/dashboard" && npm run lint
```

Expected: exit code `0`.

- [ ] **Step 4: Run build**

Run:

```bash
cd "ProbaLab/dashboard" && npm run build
```

Expected: exit code `0`. Existing Vite chunk warnings are acceptable if no new errors appear.

- [ ] **Step 5: Check git diff**

Run:

```bash
git diff --stat -- ProbaLab/dashboard/src/pages/v2/HomeV2.tsx ProbaLab/dashboard/src/pages/v2/HomeV2.test.tsx ProbaLab/dashboard/src/components/v2/home/SafeOfTheDayCard.tsx ProbaLab/dashboard/src/components/v2/home/SafeOfTheDayCard.test.tsx ProbaLab/dashboard/src/components/v2/home/ValueBetsTeaser.tsx ProbaLab/dashboard/src/pages/v2/MatchDetailV2.tsx ProbaLab/dashboard/src/pages/v2/MatchDetailV2.test.tsx ProbaLab/dashboard/src/components/v2/match-detail/RecoCard.tsx ProbaLab/dashboard/src/components/v2/match-detail/RecoCard.test.tsx ProbaLab/dashboard/src/components/v2/match-detail/ValueBetsList.tsx ProbaLab/tasks/lessons.md
```

Expected: only the scoped UX/UI files plus lesson changed for this tranche.

---

## Self-Review

- Spec coverage: tasks cover connected home, match detail, pronos as secondary, IA/content wording, premium perception, and removal of trading/value-first vocabulary.
- Scope: no backend, no routing, no pricing, no visitor landing refactor in this tranche.
- Placeholder scan: no `TBD`, `TODO`, or unresolved implementation placeholders.
- Type consistency: no new API types; all changes use existing `Recommendation`, `MarketProb`, `BookOdd`, and test fixtures.
- Commit note: do not create a git commit unless the user explicitly asks for one.
