# TODO — Audit Findings

## Corrigé (2026-03-19)
- [x] Bug #1 : Discontinuité ρ scaling (coeff 0.4→0.6)
- [x] Bug #2 : MAX_GOALS_GRID 7→10 (masse 88.9%→99.2%)
- [x] Bug #3 : Double comptage nuls CL (euro_boost skip si draw calibré)
- [x] Bug #4 : Ensemble class balancing (sample_weight ajouté)
- [x] Bug #5 : Seuil NaN ML (>40% → skip)
- [x] Bug #6 : poisson_grid sum forcé à 100
- [x] Bug #7 : Draw floor ELO 0.10→0.15
- [x] Bug #8 : eval_set leak (validation set séparé)
- [x] Bug #9 : Platt sanity check (|a|>20 → skip)
- [x] Bug #11 : RestrictedUnpickler resserré (préfixes spécifiques)
- [x] Bug #12 : HOME_ELO_ADVANTAGE per-league

## Corrigé (2026-03-22) — Fiabilité
- [x] brain.py : sanitisation noms d'équipes dans prompts Gemini (anti-injection)
- [x] brain.py : retry Gemini (1 retry + sleep 2s) pour erreurs transitoires
- [x] brain.py : warning log si WEIGHT_AI > 0 en Phase 1 (100% stats)
- [x] brain.py : extraction JSON plus robuste (itère sur blocs valides avant greedy)
- [x] brain.py : AIFeatures validation log warning→error avec noms d'équipes
- [x] bankroll.py : minimum bet 0.50€ validation dans place_bet
- [x] ticket_generator.py : documentation des discount factors (0.85, 0.90)
- [x] ticket_generator.py : clamping probabilité > 100% dans calculate_implied_odds
- [x] notifications.py : html.escape() sur variables injectées dans HTML Telegram

## Corrigé (2026-03-22) — Sécurité API
- [x] nhl.py : pickle.load → RestrictedUnpickler (whitelist numpy/pandas/sklearn/xgboost/lightgbm)
- [x] main.py : CORS — validation URLs + warning si ALLOWED_ORIGINS non défini
- [x] main.py : subprocess command injection — whitelist _ALLOWED_PIPELINE_MODES + Literal dans schema
- [x] main.py + nhl.py + trigger.py : error exposure — str(e) → message générique, log côté serveur
- [x] main.py : rate limiting @_rate_limit sur endpoints admin/cron (10/min) et best-bets/predictions (30/min)
- [x] main.py : CRON_SECRET — hmac.compare_digest (timing-safe)
- [x] schemas.py : regex dates, Literal pour sport/mode/result, max_length pour strings
- [x] stripe_webhook.py : idempotency — pre-check SELECT + pgcode 23505 fallback

## Corrigé (2026-03-22) — Data Pipeline
- [x] fetchers : silent `pass` → logger.error sur tous les except vides (history, context, live, matches)
- [x] fetchers : logger.warning avant `continue` sur réponses API vides (events, lineups, stats, odds, H2H)
- [x] matches.py : .get() avec guard au lieu d'accès directs `item["fixture"]`
- [x] context.py : log mismatch H2H team names, log odds incomplètes, log weather timeout
- [x] results.py + matches.py : commentaires timezone UTC/Paris

## Corrigé (2026-03-22) — Modèles Statistiques
- [x] stats_engine.py : itération bayésienne 5→10 avec arrêt convergence (max_delta < 0.005)
- [x] stats_engine.py : draw calibration cap ±15% → ±20% par passe
- [x] stats_engine.py : soft cap 80% — redistribution proportionnelle au lieu de 40% au draw
- [x] constants.py : 5 coupes nationales ajoutées à HOME_ELO_ADVANTAGE_BY_LEAGUE
- [x] constants.py : commentaire EURO_COMP_DRAW_BOOST dead code documenté
- [x] injury_vorp.py : seuil minutes par position (GK/DEF: 100min, autres: 150min)

## Corrigé (2026-03-22) — ML Pipeline
- [x] train.py : data leakage fix — imputer fit post-split sur X_train uniquement
- [x] train.py : cross_val_score params= → fit_params= (sklearn 1.5+)
- [x] ml_predictor.py : label encoder fallback corrigé A=0, D=1, H=2
- [x] ensemble.py : idem label encoder fallback
- [x] ml_predictor.py : imputer fallback warning log

## Corrigé (2026-03-22) — Retry & Timezone
- [x] config.py : api_get_with_retry helper (retry on empty response with backoff 1s/2s)
- [x] config.py : datetime.now() -> datetime.now(timezone.utc) dans _get_current_season
- [x] history.py : events/lineups/statistics utilisent api_get_with_retry
- [x] context.py : odds/h2h utilisent api_get_with_retry
- [x] context.py : datetime.fromtimestamp(tz=timezone.utc) dans fetch_weather
- [x] matches.py : datetime.now() -> datetime.now(timezone.utc) dans fetch_and_store

## Corrigé (2026-03-22) — Atomicité Bankroll
- [x] bankroll.py : place_bet utilise RPC `place_bet_atomic` (SELECT FOR UPDATE) pour éliminer race conditions
- [x] bankroll.py : ancienne logique renommée `_place_bet_legacy` en fallback si RPC non déployée
- [x] migrations/019_atomic_place_bet.sql : fonction PostgreSQL idempotente (CREATE OR REPLACE)

## Ajouté (2026-03-22) — CI/CD & Alerting
- [x] CI : workflow remanié en 3 jobs parallèles (lint, test, type-check) — .github/workflows/ci.yml
- [x] Alerting : src/monitoring/alerting.py — Brier drift, complétude données, volume prédictions
- [x] Pipeline : run_pipeline.py full appelle run_monitoring_alerts() en fin de pipeline
- [x] API : GET /api/monitoring/health — endpoint léger de santé (counts, coverage, last prediction)
- [x] Daily pipeline : TELEGRAM secrets ajoutés pour monitoring alerts
- [x] CLI : python -m src.monitoring --alerts pour lancer les checks manuellement

## Ajouté (2026-03-22) — Calibration & Monitoring
- [x] calibrate.py : Bayesian shrinkage 1X2 (safe avec n<500, converge vers identity)
- [x] stats_engine.py : 1X2 calibration activée via calibrate_1x2_bayesian
- [x] brain.py : odds_at_prediction sauvegardé dans stats_json pour CLV tracking
- [x] backtest_clv.py : log coverage (n_matched/n_total), docstring pipeline data
- [x] data_quality.py : moniteur de qualité (coverage, odds, events, null probas)
- [x] __main__.py : --quality flag + data quality dans le rapport consolidé
- [x] constants.py : BAYESIAN_SHRINKAGE_K, BASE_RATE_HOME/DRAW/AWAY

## Restant (nécessite données ou réentraînement)
- [ ] ECE 0.13 : réentraîner calibrateur avec 500+ samples (Isotonic)
- [x] CLV tracking : coupler fixture_odds aux predictions pour mesurer CLV
- [ ] Drift monitoring : Brier dernier window 0.6502 vs moyenne 0.6197
- [ ] Réentraîner modèles ML après ces fixes (imputer post-split + fit_params + grid 10x10)
- [x] Frontend : standardiser stats_json vs top-level (helper getStatValue centralisé)
- [x] Frontend : cache API per-user (clearApiCache déjà wired sur logout)
