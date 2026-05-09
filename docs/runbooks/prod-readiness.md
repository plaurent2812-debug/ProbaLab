# Production Readiness

> Tout ce qu'il faut pour déployer, vérifier, et rollback ProbaLab sans deviner.
> Source : master plan Phase 1 (`docs/superpowers/plans/2026-04-26-top-1-france-master-plan.md`).

## Architecture déployée

| Composant | Hébergeur | Trigger build |
|---|---|---|
| API FastAPI (`uvicorn api.main:app`) | Railway service `web` (nixpacks) | push sur `main` |
| Worker (`python worker.py`) | Railway service `worker` | push sur `main` |
| Frontend Vite (`ProbaLab/dashboard`) | Vercel | push sur `main` |
| DB Postgres + RLS | Supabase project `yskpqdnidxojoclmqcxn` | migrations manuelles |

Healthcheck Railway : `GET /health` (timeout 30 s, retry 3, voir `ProbaLab/railway.toml`).

## Variables d'environnement requises

### Backend (Railway, services `web` et `worker`)

| Variable | Source | Sans valeur ? |
|---|---|---|
| `SUPABASE_URL` | Supabase project | requis — DB inaccessible |
| `SUPABASE_KEY` | Supabase service_role | requis (legacy nom, voir code) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service_role | requis pour admin/RLS bypass |
| `SUPABASE_ANON_KEY` | Supabase anon | requis pour endpoints user |
| `API_FOOTBALL_KEY` | API-Football PRO | requis — pas de fixtures football |
| `THE_ODDS_API_KEY` | The Odds API ($30/m) | requis — pas de cotes |
| `ODDS_API_KEY` | The Odds API (legacy nom) | utilisé par certains modules |
| `GEMINI_API_KEY` | Google AI Studio | requis — pas d'analyse narrative (graceful degradation) |
| `STRIPE_SECRET_KEY` | Stripe live | requis — pas d'abos premium |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook | requis — événements Stripe ignorés |
| `RESEND_API_KEY` | Resend | requis — pas d'emails transactionnels |
| `RESEND_FROM` | string | défaut `ProbaLab <noreply@probalab.fr>` |
| `TELEGRAM_BOT_TOKEN` | BotFather | requis — alertes muettes |
| `TELEGRAM_CHANNEL_ID` | string | requis pour broadcasts publics |
| `TELEGRAM_CHAT_IDS` | CSV | requis pour alertes admin/op |
| `TELEGRAM_EXPERT_BOT_TOKEN` | BotFather | optionnel — VIP channel |
| `TELEGRAM_WEBHOOK_SECRET` | random | requis si webhook Telegram exposé |
| `DISCORD_WEBHOOK_URL` | Discord webhook | optionnel |
| `OPENWEATHER_API_KEY` | OpenWeather | optionnel — feature météo désactivée sans |
| `CRON_SECRET` | random ≥ 32 chars | requis — endpoints `/trigger/*` ouverts si absent (à vérifier en code) |
| `API_SECRET_KEY` | random | requis — auth interne |
| `ALLOWED_ORIGINS` | CSV URLs | requis prod — CORS trop laxiste sinon |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_EMAIL` | webpush | requis push notifs |
| `PUSH_API_KEY` | random | requis — endpoint push protégé |
| `FOOTBALL_SEASON` | int année | optionnel — défaut calculé dynamiquement |
| `PROBALAB_ACTIVE_VARIANT` | `baseline`/string | optionnel — A/B variant ML |

### Frontend (Vercel)

| Variable | Description |
|---|---|
| `VITE_API_URL` | base URL API (ex. `https://api.probalab.fr`) |
| `VITE_SUPABASE_URL` | Supabase URL côté client |
| `VITE_SUPABASE_ANON_KEY` | clé anon (jamais service_role) |
| `VITE_FRONTEND_V2` | `true` pour activer V2, `false` pour rollback legacy |
| `VITE_API_SEASON` | saison football affichée (optionnel) |
| `VITE_STRIPE_PAYMENT_LINK` | lien Stripe checkout |
| `VITE_STRIPE_CUSTOMER_PORTAL` | lien Stripe portal |
| `VITE_TELEGRAM_VIP_LINK` | lien public canal Telegram VIP |
| `VITE_VAPID_PUBLIC_KEY` | doit matcher `VAPID_PUBLIC_KEY` backend |
| `VITE_MSW_ENABLED` | **JAMAIS `true` en prod** — uniquement E2E/preview |
| `VITE_MSW_PREVIEW` | idem |
| `VITE_E2E` | idem |

> **Garde-fou** : si `VITE_MSW_ENABLED=true` en prod, l'app sert des données fixtures. À vérifier dans Vercel avant tout déploiement.

## Smoke tests post-déploiement

À exécuter après chaque deploy Railway/Vercel. Si un seul échoue → rollback immédiat (voir section suivante).

```bash
# Backend health
curl -fsS "$API_URL/health"

# Performance summary (cache, doit répondre <1s)
curl -fsS "$API_URL/api/performance/summary?window=30"

# Matches du jour (sport principal)
curl -fsS "$API_URL/api/matches?date=$(date -u +%F)"

# Frontend root (HTML 200, pas de blank page)
curl -fsS "$APP_URL/" | grep -q '<div id="root"'
```

Vérifier ensuite manuellement (≤ 5 minutes) :

1. Ouvrir `$APP_URL/` dans un navigateur incognito, login user existant.
2. Page Home V2 : KPI Performance affichées, pas d'erreur dans la console.
3. Page Matches : au moins une ligue avec des matchs du jour.
4. Page MatchDetail sur un match avec prediction : probabilités cohérentes (somme ≈ 100 %, pas de 0 %).
5. Page Premium : prix `14,99 €/mois` partout.

## Procédures de rollback

### P0 — page blanche, login cassé, toutes les prédictions HS

**Frontend Vercel** :
1. Vercel dashboard → Deployments → précédent deploy `main` réussi → `Promote to Production`.
2. OU : `VITE_FRONTEND_V2=false` dans Vercel → redeploy → frontend legacy.
3. Vérifier le smoke `curl $APP_URL/`.

**Backend Railway** :
1. Railway dashboard → service `web` → Deployments → précédent deploy → `Rollback`.
2. Vérifier `curl $API_URL/health`.

### P1 — un sport HS, Stripe cassé, notifications muettes

1. Identifier la commit fautive : `git log --oneline -10 main`.
2. Si fix < 30 min : forward-fix sur `main` avec test de régression.
3. Sinon : revert ciblé `git revert <sha>` → push `main` → smoke.

### Migrations Supabase

- **Politique** : aucune migration ne supprime/altère une colonne en prod sans plan de rollback explicite documenté dans le PR.
- **Rollback** : restaurer le snapshot Supabase (Supabase dashboard → Database → Backups). Tester d'abord en branche.
- **Application manuelle** : certaines migrations (ex. `050_model_health_log.sql`) sont appliquées via Supabase Studio SQL editor car le MCP service-role n'a pas accès au projet ProbaLab. Procédure :
  1. Ouvrir https://supabase.com/dashboard/project/yskpqdnidxojoclmqcxn/sql
  2. Coller le contenu du fichier `ProbaLab/migrations/<nom>.sql`
  3. Exécuter
  4. Vérifier : `pytest tests/test_<nom>.py -m integration -v` doit passer

### RLS — vérification d'urgence

Si suspicion de fuite de données (user A voit ce que possède user B) :

```sql
-- Lister les tables sans RLS active
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name NOT IN (
    SELECT tablename FROM pg_tables
    WHERE schemaname = 'public' AND rowsecurity = true
  );

-- Lister les policies d'une table
SELECT * FROM pg_policies WHERE tablename = '<table>';
```

Toute table user-owned (paris, bankroll, settings, notifications) doit avoir une policy `auth.uid() = user_id`. Migration de référence : `020_enable_rls_all_tables.sql`.

## Rotation des secrets

| Secret | Fréquence cible | Procédure |
|---|---|---|
| `CRON_SECRET` | trimestrielle | voir `tasks/runbook_secret_rotation.md` (à créer si absent) — supporter 2 secrets en parallèle pendant la transition |
| `STRIPE_WEBHOOK_SECRET` | sur incident | rotate dans Stripe dashboard → mettre à jour Railway → tester un webhook |
| Tokens Telegram | sur incident | revoke + new via BotFather |
| Supabase service_role | sur incident grave | regenerate dans dashboard → mettre à jour TOUS les services |

## Garde-fous non négociables (CLAUDE.md)

- 0 secret en clair dans le repo. `.env` jamais commité (vérifier `.gitignore`).
- Tout endpoint admin protégé par `Depends(verify_internal_auth)`.
- RLS active sur toute table user-owned, avec policy testée.
- Tests verts obligatoires avant push (voir `quality-gates.md`).
- Tout endpoint consommé par le frontend V2 doit avoir un contract test.
- ErrorBoundary à la racine de l'app React (vérifié dans `AppV2.tsx`).

## Références

- Plan : `docs/superpowers/plans/2026-04-26-top-1-france-master-plan.md` (Phase 1)
- Quality gates : `docs/runbooks/quality-gates.md`
- Incident response : `docs/runbooks/incident-response.md`
- Lessons : `ProbaLab/tasks/lessons.md`
