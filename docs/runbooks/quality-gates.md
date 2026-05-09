# Quality Gates

> Source de vérité pour ce qu'il faut lancer avant de merger ou de déployer.
> Toute commande listée ici doit être identique en local et dans GitHub Actions.

## Avant tout merge sur `main`

### Backend Python — obligatoire

```bash
cd ProbaLab && python -m pytest tests/ -m "not integration" --timeout=60 \
  --cov=src --cov=api --cov-report=term-missing --cov-fail-under=21 -q
```

Attendu :
- Tous les tests verts (≥ 697 passed sur la baseline 2026-05-09).
- Aucune sortie réseau live (les probes API-Football sont marquées `integration`).
- Couverture ≥ 21 % (seuil CI courant — voir « Évolution du seuil » plus bas).

### Frontend Vitest — obligatoire

```bash
cd ProbaLab/dashboard && VITE_API_URL=http://localhost:8000 npm run test:ci
```

Attendu :
- Tous les tests Vitest verts (≥ 744 passed sur la baseline 2026-05-09).
- MSW handlers et hooks partagent la même base URL via `VITE_API_URL`.

### Lint Python — obligatoire

```bash
cd ProbaLab && ruff check src/ api/ tests/
cd ProbaLab && ruff format --check src/ api/ tests/
```

### Whitespace

```bash
git diff --check
```

### TypeScript

```bash
# V2 production — obligatoire à terme (voir master plan Phase 0.3)
cd ProbaLab/dashboard && npx tsc --noEmit --project tsconfig.v2.json

# Legacy global — tracké comme dette, ne bloque pas le merge V2
cd ProbaLab/dashboard && npx tsc --noEmit
```

## Manuel / opt-in

### Probes API-Football live

```bash
RUN_LIVE_API_TESTS=1 cd ProbaLab && python -m pytest \
  tests/test_api_cs.py tests/test_api_cs2.py tests/test_api_cs_l1.py \
  tests/test_cleansheets.py tests/test_cs_fields.py -m integration -q
```

Réservé : audit ponctuel, debug d'un provider, vérification post-changement de plan API.

### Migration Supabase à appliquer manuellement

Pour les migrations DDL livrées dans `ProbaLab/migrations/`, l'application reste manuelle via Supabase Studio (le service role MCP n'a pas toujours accès). Voir la procédure spécifique dans `prod-readiness.md`.

### Playwright E2E

```bash
cd ProbaLab/dashboard && npm run e2e
```

Attendu : exécuté en CI sur chaque PR. En local, utile après tout changement V2 visible (Home, Matches, MatchDetail, Premium, Account).

## Évolution du seuil de couverture

`--cov-fail-under=21` reflète l'état historique du repo, pas la cible. Le master plan vise > 60 % global et > 80 % sur `best_bets` + `prediction_blender`. Toute hausse de seuil :

1. Doit être précédée d'un push qui démontre la couverture atteinte.
2. Se modifie dans `.github/workflows/ci.yml` (job `test`).
3. Ne doit jamais redescendre — un PR qui régresse la couverture est refusé.

## Si un test devient flaky

1. Reproduire en boucle locale : `pytest tests/<file>::<test> --count=20` (pytest-repeat) ou Vitest `--run --repeat=20`.
2. Si la flakyness vient d'un mock partagé : `resetHandlers` dans `afterEach` côté MSW, fixture `function`-scoped côté pytest.
3. Si la flakyness vient d'un timing : pas de `setTimeout` arbitraire — utiliser `waitFor`/`waitForURL` côté Playwright et `await waitFor(...)` côté Vitest.
4. Quarantaine temporaire interdite sans ticket de suivi associé dans `tasks/lessons.md`.

## Quand un test live est nécessaire pour debug

- Toujours `-m integration` + `RUN_LIVE_API_TESTS=1`.
- Jamais ajouté à la commande CI standard.
- Si un test live devient indispensable au quotidien : transformer en test unitaire avec un mock fidèle plutôt que d'élargir la commande standard.

## Références

- CI : `.github/workflows/ci.yml`
- Plan source : `docs/superpowers/plans/2026-04-26-top-1-france-master-plan.md`, Phase 0
- Lessons : `ProbaLab/tasks/lessons.md`
