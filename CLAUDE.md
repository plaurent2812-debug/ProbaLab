# ProbaLab — Instructions projet

## Stack
- **Backend** : FastAPI (Python) + Uvicorn
- **Frontend** : React 19 + Vite + Tailwind CSS 4 + Radix UI (shadcn pattern)
- **Base de données** : Supabase (PostgreSQL + RLS strict)
- **ML** : XGBoost, LightGBM, scikit-learn, Optuna, Pandas, NumPy
- **IA générative** : Google Gemini (analyses narratives)
- **Jobs** : APScheduler (cron) + Trigger.dev (remote jobs)
- **Messagerie** : Telegram bot, Discord webhooks, Resend
- **Paiements** : Stripe (abonnements premium)
- **Déploiement** : Railway (nixpacks) + GitHub Actions CI

## Périmètre métier
Plateforme de prédictions sportives avec value betting
- **Football** : 8 ligues (L1, L2, PL, La Liga, Serie A, Bundesliga, UCL, UEL)
- **NHL** : secondaire
- Marchés : 1X2, Double Chance, BTTS, O/U, Handicaps, Score Exact, Buteurs
- Value betting : ROI + Kelly Criterion
- Combo tickets : Safe / Fun / Jackpot
- Suivi bankroll, P&L, évaluation post-match

## Architecture prédictions (3 couches)
1. **70% stats** : Dixon-Coles, ELO, 50+ features
2. **ML calibré** : XGBoost ensemble
3. **30% IA** : analyse narrative Gemini

## Conventions
- Supabase RLS strict — vérifier les policies avant toute requête
- Timezones : tout en UTC sans exception
- fixture_id : typage strict (pas de mélange int/str)
- Nommage probabilités : respecter la convention établie (voir lessons.md)
- Double Chance : respecter le naming spécifique (voir lessons.md)
- 381 tests — ne jamais merger sans tests verts

## Outils MCP
- **Context7** : consulter avant toute implémentation touchant une API ou librairie
- **Supabase MCP** : inspecter schéma, requêter DB, gérer RLS directement

## État actuel
- En production, stabilisation active
- Phases 1-3 terminées (troncature, types, combos, timezones, Double Chance)
- Audit sécurité mars 2026 (60+ fixes appliqués)
- 30 leçons documentées dans `tasks/lessons.md` — **lire en priorité**

## Pièges documentés (voir tasks/lessons.md pour le détail)
- Timezones : toujours UTC, jamais de conversion implicite
- fixture_id : typage strict partout
- Combos : logique de résolution spécifique, ne pas simplifier
- RLS Supabase : tester les policies après chaque migration
- Gemini : quota et latence — ne pas bloquer le pipeline ML dessus

## Déploiement
- Railway avec nixpacks — vérifier le Procfile avant tout push
- GitHub Actions CI — les tests doivent passer en local avant push
