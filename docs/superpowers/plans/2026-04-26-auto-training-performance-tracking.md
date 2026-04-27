# ProbaLab Auto-Training + Performance Tracking Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Créer une vraie boucle d'apprentissage automatique pour que ProbaLab s'améliore avec les résultats réels, tout en suivant précisément les performances par sport, marché, modèle et période.

**Architecture:** Utiliser une boucle MLOps batch contrôlée : résultats réels -> `prediction_results` -> évaluation quotidienne -> décision retrain -> entraînement candidat -> backtest holdout/walk-forward -> promotion ou rejet -> tracking public/admin. Ne jamais promouvoir automatiquement un modèle qui dégrade Brier, log loss, ECE, CLV ou data completeness.

**Tech Stack:** FastAPI, Supabase, Trigger.dev Cloud, Python training pipeline, XGBoost, LightGBM, scikit-learn, Optuna, Pytest, React V2 dashboard.

---

## Supabase Application Status

Migration file created locally:

```text
ProbaLab/migrations/060_mlops_model_registry.sql
```

Attempted CLI application on 2026-04-26:

```bash
supabase projects list
```

Result:

```text
Access token not provided. Supply an access token by running supabase login or setting the SUPABASE_ACCESS_TOKEN environment variable.
```

Action required before applying remotely:

```bash
supabase login
```

or:

```bash
export SUPABASE_ACCESS_TOKEN=...
```

Then link/push the migration to project `yskpqdnidxojoclmqcxn`, or paste the SQL migration in Supabase Studio.

---

## Vision Produit

Le système doit donner à ProbaLab une boucle d'amélioration mesurable :

1. Chaque prédiction est horodatée et liée à un `model_version`.
2. Après les matchs, les résultats réels alimentent `prediction_results`.
3. Chaque jour, l'app mesure Brier, log loss, ECE, ROI, CLV, accuracy et fallback rate.
4. Si assez de nouvelles données existent ou si un drift est détecté, un entraînement candidat est lancé.
5. Le modèle candidat est testé sur un holdout temporel non vu.
6. Il est promu seulement s'il bat le modèle actif selon des règles strictes.
7. Toutes les décisions sont historisées.
8. L'admin voit la santé modèle, et les utilisateurs voient un track record honnête.

Ce n'est pas du "réentraîner dès qu'un match se termine". C'est volontaire : un modèle qui apprend trop vite sur peu de matchs sur-réagit au bruit. ProbaLab doit apprendre régulièrement, mais avec des garde-fous.

## Etat Existant

Déjà présent :

- `src/training/train.py` entraîne plusieurs modèles football et contient déjà une logique de non-promotion si le nouveau Brier est pire.
- `src/monitoring/brier_monitor.py` calcule Brier, log loss, ECE et drift rolling.
- `src/monitoring/drift_detector.py` compare Brier 7j vs 30j.
- `src/monitoring/alerting.py` alerte sur Brier, data completeness, volume et CLV.
- `src/monitoring/feature_drift.py` teste le drift des features avec KS test.
- `run_pipeline.py` persiste déjà un snapshot partiel dans `model_health_log`.
- `trigger-worker/src/trigger/mlEvaluation.ts` et `mlTraining.ts` existent, mais contiennent des commentaires contradictoires sur APScheduler vs Trigger.dev.
- `ml_models` existe mais impose `UNIQUE(model_name)`, ce qui écrase l'historique et limite le versioning.

Manquant :

- un vrai historique des versions modèles ;
- un historique des runs de training ;
- une table de décisions promotion/rejet ;
- un scorecard par sport/marché/modèle ;
- un endpoint admin MLOps ;
- un dashboard admin clair ;
- des seuils de promotion formalisés ;
- un lien propre entre Trigger.dev et endpoints FastAPI ;
- un système de rollback modèle.

---

## Phase 1: Schéma MLOps Supabase

**Outcome:** Les modèles ne sont plus seulement écrasés dans `ml_models`; chaque run, version et décision devient traçable.

**Files:**
- Create: `ProbaLab/migrations/060_mlops_model_registry.sql`
- Modify: `ProbaLab/tasks/todo.md`
- Test: `ProbaLab/tests/test_migrations_mlops.py`

- [ ] **Step 1.1: Create model training runs table**

Créer une migration avec :

```sql
create table if not exists model_training_runs (
    id uuid primary key default gen_random_uuid(),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    status text not null check (status in ('running','success','failed','rejected','promoted')),
    trigger_reason text not null check (trigger_reason in ('scheduled','drift','manual','new_data')),
    sport text not null check (sport in ('football','nhl')),
    market text not null,
    train_from timestamptz,
    train_until timestamptz,
    holdout_from timestamptz,
    holdout_until timestamptz,
    training_samples integer not null default 0,
    holdout_samples integer not null default 0,
    error_message text,
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_model_training_runs_started_at
    on model_training_runs(started_at desc);

create index if not exists idx_model_training_runs_sport_market
    on model_training_runs(sport, market, started_at desc);
```

- [ ] **Step 1.2: Create model versions table**

Ajouter :

```sql
create table if not exists model_versions (
    id uuid primary key default gen_random_uuid(),
    training_run_id uuid references model_training_runs(id) on delete set null,
    model_name text not null,
    model_version text not null,
    sport text not null check (sport in ('football','nhl')),
    market text not null,
    model_type text not null,
    artifact_table text not null default 'ml_models',
    artifact_ref text not null,
    feature_names text[] not null default '{}',
    feature_hash text,
    train_window jsonb not null default '{}'::jsonb,
    metrics jsonb not null default '{}'::jsonb,
    is_active boolean not null default false,
    promoted_at timestamptz,
    created_at timestamptz not null default now(),
    unique(model_name, model_version)
);

create unique index if not exists idx_model_versions_one_active
    on model_versions(model_name)
    where is_active = true;

create index if not exists idx_model_versions_sport_market
    on model_versions(sport, market, created_at desc);
```

- [ ] **Step 1.3: Create model performance snapshots table**

Ajouter :

```sql
create table if not exists model_performance_snapshots (
    id bigserial primary key,
    recorded_at timestamptz not null default now(),
    sport text not null check (sport in ('football','nhl')),
    market text not null,
    model_name text not null,
    model_version text,
    window_days integer not null check (window_days in (1,7,30,90)),
    sample_size integer not null default 0,
    accuracy numeric,
    brier numeric,
    log_loss numeric,
    ece numeric,
    roi numeric,
    clv_mean numeric,
    clv_positive_pct numeric,
    fallback_rate numeric,
    data_completeness_pct numeric,
    metrics jsonb not null default '{}'::jsonb
);

create index if not exists idx_model_perf_snapshots_lookup
    on model_performance_snapshots(sport, market, model_name, window_days, recorded_at desc);
```

- [ ] **Step 1.4: Create promotion decisions table**

Ajouter :

```sql
create table if not exists model_promotion_decisions (
    id bigserial primary key,
    decided_at timestamptz not null default now(),
    training_run_id uuid references model_training_runs(id) on delete set null,
    model_name text not null,
    candidate_version text not null,
    active_version text,
    decision text not null check (decision in ('promote','reject','manual_review')),
    reason text not null,
    candidate_metrics jsonb not null default '{}'::jsonb,
    active_metrics jsonb not null default '{}'::jsonb,
    thresholds jsonb not null default '{}'::jsonb,
    decided_by text not null default 'system'
);
```

- [ ] **Step 1.5: Enable RLS**

Ajouter :

```sql
alter table model_training_runs enable row level security;
alter table model_versions enable row level security;
alter table model_performance_snapshots enable row level security;
alter table model_promotion_decisions enable row level security;

create policy "service_role_all_model_training_runs"
    on model_training_runs for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "service_role_all_model_versions"
    on model_versions for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "service_role_all_model_performance_snapshots"
    on model_performance_snapshots for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

create policy "service_role_all_model_promotion_decisions"
    on model_promotion_decisions for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');
```

**Done Criteria:**
- Les migrations créent un registre modèle complet.
- RLS est activée.
- Le backend service role peut écrire.
- Les utilisateurs anonymes ne peuvent pas lire ces tables privées.

---

## Phase 2: Evaluation Quotidienne Des Performances

**Outcome:** Le taux de performance est suivi automatiquement tous les jours, par sport, marché, modèle, version et fenêtre temporelle.

**Files:**
- Create: `ProbaLab/src/mlops/performance_tracker.py`
- Modify: `ProbaLab/src/monitoring/brier_monitor.py`
- Test: `ProbaLab/tests/test_mlops_performance_tracker.py`

- [ ] **Step 2.1: Create `compute_market_metrics`**

Créer une fonction pure :

```python
def compute_market_metrics(rows: list[dict], market: str) -> dict:
    """Return accuracy, brier, log_loss, ece, roi, clv and sample_size."""
```

Elle doit gérer :
- aucun row -> `sample_size=0`, métriques `None`;
- 1X2 multiclass;
- marchés binaires BTTS/O/U/NHL moneyline;
- probas en pourcentage ou ratio selon la source;
- résultats manquants ignorés.

- [ ] **Step 2.2: Create snapshot builder**

Ajouter :

```python
def build_performance_snapshot(
    *,
    sport: str,
    market: str,
    model_name: str,
    model_version: str | None,
    window_days: int,
) -> dict:
    ...
```

La fonction charge `prediction_results` sur la fenêtre UTC et retourne une ligne prête à insérer dans `model_performance_snapshots`.

- [ ] **Step 2.3: Persist daily snapshots**

Ajouter :

```python
def persist_daily_performance_snapshots() -> dict:
    ...
```

Couverture minimale :
- football 1X2;
- football BTTS;
- football over_25;
- NHL moneyline;
- NHL totals si données disponibles.

Fenêtres :
- 1 jour;
- 7 jours;
- 30 jours;
- 90 jours.

- [ ] **Step 2.4: Add tests**

Tests requis :
- Brier 1X2 correct sur 3 lignes synthétiques;
- log loss borné avec epsilon;
- ECE retourne `None` si sample insuffisant;
- ROI calcule correctement WIN/LOSS/VOID;
- CLV calcule la moyenne quand closing odds disponibles;
- snapshot ignore les résultats non terminés;
- snapshot sépare football et NHL.

Run:

```bash
cd ProbaLab && python -m pytest tests/test_mlops_performance_tracker.py -q
```

**Done Criteria:**
- Un run quotidien insère des métriques exploitables.
- L'admin peut suivre le taux de perf par fenêtre.
- Les métriques sont séparées par sport/marché/modèle.

---

## Phase 3: Décision De Retraining

**Outcome:** Le système sait quand réentraîner sans le faire trop souvent.

**Files:**
- Create: `ProbaLab/src/mlops/retrain_policy.py`
- Test: `ProbaLab/tests/test_mlops_retrain_policy.py`

- [ ] **Step 3.1: Define retrain policy**

Créer :

```python
def should_retrain(context: dict) -> dict:
    """Return decision, reasons and trigger_reason for an auto-training run."""
```

Règles :
- retrain hebdomadaire planifié si au moins 100 nouveaux résultats football ou 50 nouveaux résultats NHL;
- retrain anticipé si Brier 7j > Brier 30j + 0.02 avec sample suffisant;
- retrain anticipé si CLV 7j < -1%;
- retrain anticipé si ECE 30j > 0.08;
- pas de retrain si data completeness < 80%;
- pas de retrain si trop peu de nouveaux résultats;
- `manual` peut forcer un run candidat, mais pas forcer la promotion.

- [ ] **Step 3.2: Add cooldown**

Règle :
- pas plus d'un auto-training par sport/marché toutes les 48h;
- un run `manual` admin peut contourner le cooldown uniquement pour créer un candidat.

- [ ] **Step 3.3: Add tests**

Tests :
- scheduled + assez de données -> retrain;
- scheduled + pas assez de données -> no retrain;
- drift Brier -> retrain;
- CLV négative -> retrain;
- data completeness mauvaise -> no retrain;
- cooldown actif -> no retrain;
- manual -> candidate allowed.

**Done Criteria:**
- Le système apprend quand il y a un signal, pas sur du bruit.
- Les retrains sont explicables.
- Chaque décision produit une raison lisible.

---

## Phase 4: Training Candidat Et Versioning

**Outcome:** Chaque entraînement crée un candidat versionné, sans écraser le modèle actif.

**Files:**
- Create: `ProbaLab/src/mlops/training_orchestrator.py`
- Modify: `ProbaLab/src/training/train.py`
- Modify: `ProbaLab/src/training/train_meta.py`
- Test: `ProbaLab/tests/test_mlops_training_orchestrator.py`

- [ ] **Step 4.1: Wrap training in a run record**

Créer :

```python
def start_training_run(*, sport: str, market: str, trigger_reason: str) -> dict:
    ...
```

Elle insère `model_training_runs(status='running')`.

- [ ] **Step 4.2: Train candidate without activating**

Modifier le training pour produire :
- `model_version`: `"{model_name}_{YYYYMMDDHHMMSS}_{short_hash}"`;
- `is_active=False`;
- métriques holdout;
- artifact ref.

Important : ne pas faire `upsert(... on_conflict="model_name")` pour les candidats. Garder l'historique.

- [ ] **Step 4.3: Store candidate version**

Insérer dans `model_versions` :
- sport;
- market;
- model_name;
- model_version;
- feature_names;
- feature_hash;
- train window;
- metrics;
- artifact ref.

- [ ] **Step 4.4: Mark run success or failed**

Toujours clôturer `model_training_runs` :
- `success` si candidat créé;
- `failed` avec `error_message` si exception;
- `rejected` ou `promoted` après décision.

- [ ] **Step 4.5: Add tests**

Tests :
- un run est créé avant entraînement;
- une exception marque le run failed;
- le candidat n'est pas actif par défaut;
- `model_version` est unique;
- deux runs n'écrasent pas l'historique.

**Done Criteria:**
- Aucun nouveau modèle ne remplace le modèle actif avant décision.
- Chaque modèle candidat est historisé.
- Chaque échec est visible.

---

## Phase 5: Promotion, Rejet Et Rollback

**Outcome:** ProbaLab promeut uniquement les modèles meilleurs, et peut revenir en arrière.

**Files:**
- Create: `ProbaLab/src/mlops/promotion.py`
- Modify: `ProbaLab/src/models/ml_predictor.py`
- Test: `ProbaLab/tests/test_mlops_promotion.py`

- [ ] **Step 5.1: Define promotion thresholds**

Créer des seuils par marché :

```python
PROMOTION_THRESHOLDS = {
    "football:1x2": {
        "min_holdout_samples": 300,
        "max_brier_regression": 0.002,
        "max_log_loss_regression": 0.005,
        "max_ece": 0.08,
        "min_clv_delta": -0.005,
    },
    "nhl:moneyline": {
        "min_holdout_samples": 150,
        "max_brier_regression": 0.003,
        "max_log_loss_regression": 0.007,
        "max_ece": 0.10,
        "min_clv_delta": -0.007,
    },
}
```

- [ ] **Step 5.2: Compare candidate vs active**

Créer :

```python
def decide_promotion(candidate: dict, active: dict | None) -> dict:
    ...
```

Décisions :
- `promote` si candidat meilleur ou équivalent dans tolérance et sample suffisant;
- `reject` si Brier/log loss/ECE/CLV dégradent;
- `manual_review` si métriques mixtes ou sample insuffisant.

- [ ] **Step 5.3: Promote atomically**

Dans une transaction ou séquence sûre :
- désactiver ancienne version active du même `model_name`;
- activer candidate;
- mettre `promoted_at`;
- enregistrer `model_promotion_decisions`;
- conserver ancienne version pour rollback.

- [ ] **Step 5.4: Rollback**

Créer :

```python
def rollback_model(model_name: str, target_version: str | None = None) -> dict:
    ...
```

Si `target_version` est absent, revenir à la dernière version active précédente.

- [ ] **Step 5.5: Add tests**

Tests :
- candidat meilleur -> promote;
- candidat pire Brier -> reject;
- candidat sample insuffisant -> manual_review;
- rollback restaure version précédente;
- une seule version active par `model_name`.

**Done Criteria:**
- Le système peut apprendre sans casser la production.
- Les décisions sont auditées.
- Rollback modèle possible sans redéployer l'app.

---

## Phase 6: Endpoints Trigger.dev Et Admin

**Outcome:** Trigger.dev pilote la boucle automatique; l'admin peut lancer/observer sans accès shell.

**Files:**
- Modify: `ProbaLab/api/routers/trigger.py`
- Create/modify: `ProbaLab/api/routers/admin_mlops.py`
- Modify: `ProbaLab/api/main.py`
- Modify: `ProbaLab/trigger-worker/src/trigger/mlEvaluation.ts`
- Modify: `ProbaLab/trigger-worker/src/trigger/mlTraining.ts`
- Test: `ProbaLab/tests/test_api/test_mlops_endpoints.py`

- [ ] **Step 6.1: Add trigger endpoint for evaluation**

Endpoint :

```http
POST /api/trigger/mlops/evaluate
```

Auth :
- `Depends(verify_trigger_auth)`.

Action :
- persist performance snapshots;
- run alerting;
- return counts and alerts.

- [ ] **Step 6.2: Add trigger endpoint for auto-training decision**

Endpoint :

```http
POST /api/trigger/mlops/auto-train
```

Body :

```json
{
  "sport": "football",
  "market": "1x2",
  "trigger_reason": "scheduled"
}
```

Action :
- call `should_retrain`;
- if false, return decision;
- if true, create candidate run;
- decide promotion;
- return promoted/rejected/manual_review.

- [ ] **Step 6.3: Add admin read endpoints**

Endpoints :

```http
GET /api/admin/mlops/health
GET /api/admin/mlops/runs
GET /api/admin/mlops/models
GET /api/admin/mlops/performance?sport=football&market=1x2&window=30
```

- [ ] **Step 6.4: Add admin action endpoints**

Endpoints :

```http
POST /api/admin/mlops/train
POST /api/admin/mlops/promote
POST /api/admin/mlops/rollback
```

Auth :
- admin only.

- [ ] **Step 6.5: Fix Trigger.dev source of truth**

Aligner les commentaires et tasks :
- Trigger.dev Cloud est le scheduler prod;
- APScheduler est dormant;
- pas de commentaire "consolidated into worker.py" sur les tasks actives.

Schedules recommandés :
- daily evaluation: `0 4 * * *`;
- auto-training football: `0 2 * * 5`;
- auto-training NHL: `30 2 * * 5`;
- drift-triggered checks: after daily evaluation.

**Done Criteria:**
- Trigger.dev lance l'évaluation quotidienne.
- Trigger.dev peut lancer un retrain candidat.
- L'admin voit runs, modèles, décisions et performances.
- Les endpoints sont authentifiés.

---

## Phase 7: Dashboard Performance Et Apprentissage

**Outcome:** Tu peux voir si l'app apprend et si ses probas s'améliorent.

**Files:**
- Create: `ProbaLab/dashboard/src/pages/v2/admin/ModelHealthV2.tsx`
- Create: `ProbaLab/dashboard/src/hooks/v2/useModelHealth.ts`
- Create: `ProbaLab/dashboard/src/types/v2/mlops.ts`
- Test: `ProbaLab/dashboard/src/pages/v2/admin/ModelHealthV2.test.tsx`

- [ ] **Step 7.1: Model health overview**

Afficher :
- modèle actif par sport/marché;
- dernière version;
- dernier entraînement;
- prochaine fenêtre de retrain;
- status global: healthy / watch / degraded.

- [ ] **Step 7.2: Performance charts**

Afficher par sport/marché :
- Brier 7d/30d/90d;
- log loss;
- ECE;
- CLV;
- ROI;
- sample size;
- fallback rate.

- [ ] **Step 7.3: Training runs table**

Colonnes :
- started_at UTC;
- sport;
- market;
- trigger_reason;
- status;
- training_samples;
- holdout_samples;
- decision;
- reason.

- [ ] **Step 7.4: Admin actions**

Boutons :
- lancer entraînement candidat;
- promouvoir si manual_review;
- rollback;
- relancer évaluation quotidienne.

Toujours afficher confirmation avant action destructive.

- [ ] **Step 7.5: Public track record integration**

La page publique doit afficher :
- Brier 30j;
- CLV 30j;
- ROI 90j;
- sample size;
- last update UTC;
- disclaimer "les performances passées ne garantissent pas les résultats futurs".

**Done Criteria:**
- Le suivi perf est visible admin.
- Une partie crédible est visible publiquement.
- Les métriques sont compréhensibles sans jargon excessif.

---

## Phase 8: Tests Et Garde-Fous

**Outcome:** La boucle d'apprentissage est testée comme un système critique.

**Files:**
- Test: `ProbaLab/tests/test_mlops_*.py`
- Test: `ProbaLab/tests/test_api/test_mlops_endpoints.py`
- Test: `ProbaLab/dashboard/src/**/*.test.tsx`

- [ ] **Step 8.1: Unit tests**

Couverture :
- metrics;
- retrain policy;
- promotion;
- rollback;
- training run lifecycle.

- [ ] **Step 8.2: API contract tests**

Vérifier :
- endpoints trigger protégés;
- endpoints admin protégés;
- response shape stable;
- erreurs propres si modèle absent.

- [ ] **Step 8.3: Integration tests**

Créer un scénario :
- ancien modèle actif;
- candidat meilleur;
- promotion;
- snapshot performance;
- rollback.

- [ ] **Step 8.4: Frontend tests**

Tester :
- empty state;
- degraded model state;
- running training state;
- rejected candidate state;
- rollback confirmation modal.

**Done Criteria:**
- Aucune promotion sans test.
- Aucun endpoint MLOps public.
- Les états critiques sont visibles côté UI.

---

## Roadmap D'Exécution

### Semaine 1: Registre + Tracking

- [ ] Migration `model_training_runs`.
- [ ] Migration `model_versions`.
- [ ] Migration `model_performance_snapshots`.
- [ ] Migration `model_promotion_decisions`.
- [ ] `performance_tracker.py`.
- [ ] Tests métriques.

### Semaine 2: Décision + Training Candidat

- [ ] `retrain_policy.py`.
- [ ] `training_orchestrator.py`.
- [ ] adaptation `train.py` pour candidats non actifs.
- [ ] tests run lifecycle.

### Semaine 3: Promotion + Trigger.dev

- [ ] `promotion.py`.
- [ ] endpoints trigger.
- [ ] endpoints admin.
- [ ] tasks Trigger.dev alignées.
- [ ] tests API.

### Semaine 4: Dashboard + Public Proof

- [ ] page admin Model Health.
- [ ] hooks frontend MLOps.
- [ ] public track record enrichi.
- [ ] tests frontend.
- [ ] smoke test prod.

---

## Definition Of Done

Le système est complet quand :

- chaque prédiction stocke un `model_version`;
- chaque résultat final alimente `prediction_results`;
- chaque jour crée des snapshots de performance;
- chaque modèle candidat est versionné;
- aucun modèle candidat n'est actif par défaut;
- les promotions sont décidées par règles mesurables;
- les rejets sont historisés avec raison;
- rollback modèle fonctionne;
- dashboard admin montre santé, runs, versions et performance;
- track record public affiche Brier, CLV, ROI, sample size et last update UTC;
- Trigger.dev orchestre evaluation + auto-training;
- les suites backend/frontend restent vertes.
