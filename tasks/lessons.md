# Lessons Learned

| Date | Problème | Règle |
|------|----------|-------|
| 2026-03-19 | Rho scaling discontinu : interpolation linéaire avec coefficient 0.4 au lieu de 0.6, saut de 22% à xG=3.5 | Toujours vérifier la continuité aux bornes des interpolations linéaires par morceaux |
| 2026-03-19 | poisson_grid retournait sum≠100 (99 ou 101) — arrondis indépendants de 3 probas | Pour N probas sommant à 100%, toujours forcer le dernier = 100 - somme(autres) |
| 2026-03-19 | MAX_GOALS_GRID=7 : 11% de masse Poisson perdue à xG=4.0. Grid=10 ramène à 0.8% | Dimensionner les grilles pour capturer ≥99% de la masse aux valeurs extrêmes autorisées |
| 2026-03-19 | Double comptage nuls CL : draw calibration cible déjà le taux historique, euro_boost ajoutait +4% en plus | Quand un paramètre est déjà calibré sur des données historiques, ne pas ajouter de boost ad hoc sur le même signal |
| 2026-03-19 | Ensemble sans class balancing : les 3 base learners ignoraient le déséquilibre H/D/A | Vérifier que TOUS les modèles d'un pipeline reçoivent sample_weight, pas seulement le standalone |
| 2026-03-19 | eval_set=(X_test, y_test) dans ensemble : le modèle voit le test set pendant l'entraînement | Toujours utiliser un validation set séparé pour l'early stopping, jamais le test set |
| 2026-03-19 | RestrictedUnpickler startswith("sklearn") trop large : n'importe quel sous-module sklearn autorisé | Whitelist par préfixes spécifiques, pas par un startswith global |
