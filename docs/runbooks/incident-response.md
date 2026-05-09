# Incident Response

> Comment trier, communiquer, et fermer un incident sur ProbaLab.
> Source : master plan Phase 1 (`docs/superpowers/plans/2026-04-26-top-1-france-master-plan.md`).

## Niveaux de sévérité

| Niveau | Définition | SLA détection → action | Exemples |
|---|---|---|---|
| **P0** | Indisponibilité totale ou risque légal/sécurité | < 15 min | page blanche, login HS, toutes prédictions HS, corruption DB, fuite RLS, secret leak |
| **P1** | Fonctionnalité critique HS sur un périmètre | < 1 h | un sport HS, Stripe cassé, notifications muettes 24 h+, pipeline ML qui ne tourne pas |
| **P2** | Dégradation visible mais non bloquante | < 1 jour ouvré | page lente, cotes obsolètes < 4 h, copy incorrect, erreur admin non bloquante |
| **P3** | Bug visible mais sans impact métier mesurable | backlog priorisé | typo, micro-régression UI, log bruyant |

## Triage en 5 minutes

À la détection (alerte Telegram, mail user, monitoring) :

1. **Reproduire** : ouvrir `$APP_URL/` en incognito + console ouverte.
2. **Périmètre** : 1 user / 1 sport / tout le monde ?
3. **Date du dernier deploy** : `git log --oneline origin/main -10` — y a-t-il un changement récent qui pourrait expliquer ?
4. **Healthcheck** : `curl -fsS $API_URL/health`.
5. **Classer** : P0 / P1 / P2 / P3 selon le tableau ci-dessus.

Si P0 → activer la procédure P0 immédiatement, communiquer après.
Si P1+ → lancer le diagnostic puis communiquer en parallèle.

## Procédure P0

### Stopper l'hémorragie d'abord, comprendre ensuite

1. **Rollback** (voir `prod-readiness.md` section Rollback) :
   - Frontend Vercel : promote previous deploy OU `VITE_FRONTEND_V2=false`.
   - Backend Railway : rollback service `web` au deploy précédent.
2. **Smoke** : `curl -fsS $API_URL/health` + `curl -fsS $APP_URL/`.
3. **Communiquer** :
   - Telegram canal admin : « Incident P0 : <résumé 1 ligne>. Rollback en cours. ETA : <X> min. »
   - Si users impactés > 50 et durée > 30 min : message public Telegram VIP.
4. **Stabiliser** : aucun nouveau merge sur `main` tant que l'incident n'est pas clos.

### Diagnostic en parallèle

- Logs Railway : dashboard service `web` → Logs (filter level=ERROR sur la fenêtre incident).
- Logs Vercel : project → Deployments → Functions → logs.
- Sentry / monitoring : à brancher si pas déjà fait (TODO master plan Phase 1).
- Supabase : dashboard → Logs → API/Postgres pendant la fenêtre.

### Clôture P0

- [ ] Rollback ou fix forward déployé et vérifié par smoke complet.
- [ ] Cause racine identifiée (pas juste « ça remarche »).
- [ ] Post-mortem écrit dans `tasks/incidents/<date>-<slug>.md` (créer le dossier au besoin) avec :
  - timeline minute par minute,
  - cause racine,
  - pourquoi ça n'a pas été attrapé en CI/staging,
  - leçon ajoutée à `ProbaLab/tasks/lessons.md`,
  - action corrective concrète (test, alerte, garde-fou) avec deadline.

## Procédure P1

1. **Diagnostic** d'abord, fix ensuite (pas de rollback réflexe — un P1 mal géré devient P0).
2. **Reproduire** localement si possible, écrire un test rouge qui reproduit le bug (lesson 2026-04-30 sur `prediction: null` est un cas typique).
3. **Fix forward** sur une branche dédiée avec test de régression.
4. **Communiquer** une fois le fix mergé : Telegram admin + lessons mise à jour si pattern récurrent.

## Procédure P2

1. Ouvrir un ticket dans `ProbaLab/tasks/todo.md` (ou un fichier dédié si la queue grossit).
2. Prioriser dans la prochaine itération courante, pas en interrompant le scope en cours.
3. Si P2 récurrent → reclasser P1.

## Patterns d'incident à connaître

### Page blanche V2

- Causes connues : safe pick adapter cassé, ErrorBoundary absent, route lazy non chargée. Voir lessons 2026-04-22 et 2026-04-30.
- Premier réflexe : vérifier console navigateur, regarder s'il y a un `Suspense` cassé ou un `null` non géré dans `HomeV2`.

### Probabilités à 0 % NHL ou marché

- Cause connue (lesson 2026-04-30) : `/api/matches` renvoie `prediction: null` et le front convertit absent → 0.
- Vérifier : le contract test `test_v2_contracts.py` doit échouer si la shape change ; l'UI doit afficher un état « disponible bientôt » et jamais 0.

### Coverage CI qui chute brutalement

- Cause typique : nouveau code sans test, ou tests désactivés en local.
- Vérifier : `--cov-fail-under=21` en CI, augmenter le seuil seulement après push d'une vraie hausse (voir `quality-gates.md`).

### Endpoint admin non protégé

- Vérifier : `Depends(verify_internal_auth)` sur tous les `@router.{post,delete,put}` dans `api/routers/admin.py`, `mlops.py`, `trigger.py`.
- Test : `curl -X POST $API_URL/api/admin/<endpoint>` doit retourner 401/403.

### RLS contournée

- Vérifier qu'aucun endpoint user n'utilise le client `service_role`. Le client à utiliser pour les requêtes user-scoped, c'est `supabase.postgrest` avec le JWT user, pas le service role.
- Audit rapide : `grep -rn "SUPABASE_SERVICE_ROLE_KEY\|supabase_admin" api/routers/` — toute occurrence dans un endpoint user est suspecte.

### Quota Gemini saturé

- Lesson : ne pas bloquer le pipeline ML sur Gemini. Le narratif doit dégrader gracieusement (skip) si quota dépassé ou latence > seuil.
- Vérifier le timeout / circuit breaker dans `src/llm/gemini.py` (ou équivalent).

## Communication

| Canal | Quand | Ton |
|---|---|---|
| Telegram admin (`TELEGRAM_CHAT_IDS`) | tout P0/P1 | factuel, technique, ETA |
| Telegram VIP (`TELEGRAM_CHANNEL_ID`) | P0 > 30 min | court, transparent, sans jargon |
| Email Resend (broadcast) | jamais en automatique sur incident — uniquement post-mortem si users payants impactés | mesuré |

**Règle** : ne jamais cacher un incident aux users impactés. Mais ne pas notifier si le rollback a été < 5 min et invisible.

## Garde-fous post-incident

Tout post-mortem doit produire au moins un de ces livrables :

- [ ] Test de régression mergé sur `main`.
- [ ] Alerte ajoutée (monitoring, healthcheck enrichi, ou règle dans `src/monitoring/`).
- [ ] Garde-fou code (validation, type strict, ErrorBoundary, fallback).
- [ ] Leçon ajoutée à `ProbaLab/tasks/lessons.md` au format `| date | problème | règle |`.

Sans ça, l'incident se reproduira.

## Références

- Prod readiness : `docs/runbooks/prod-readiness.md`
- Quality gates : `docs/runbooks/quality-gates.md`
- Lessons : `ProbaLab/tasks/lessons.md`
- Plan : `docs/superpowers/plans/2026-04-26-top-1-france-master-plan.md` (Phase 1, Step 1.4)
