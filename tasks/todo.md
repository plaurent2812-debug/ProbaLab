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

## Restant (nécessite données ou réentraînement)
- [ ] ECE 0.13 : réentraîner calibrateur avec 500+ samples (Isotonic)
- [ ] CLV tracking : coupler fixture_odds aux predictions pour mesurer CLV
- [ ] Drift monitoring : Brier dernier window 0.6502 vs moyenne 0.6197
- [ ] VORP : améliorer distinction titulaire/remplaçant (minutes/match au lieu de minutes totales)
- [ ] Réentraîner modèles ML après ces fixes (les poids actuels utilisent l'ancien grid 7x7)
