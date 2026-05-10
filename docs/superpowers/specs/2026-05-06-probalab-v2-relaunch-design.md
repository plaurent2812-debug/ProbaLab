# Design — Relance ProbaLab V2 (refonte produit complète, moteur ML conservé)

**Date** : 2026-05-06
**Auteur** : Claude Opus 4.7 (brainstorming avec l'owner)
**Status** : ready for plan
**Branche cible** : `feat/v2-relaunch` (à créer depuis `main`)
**Worktree de travail actuel** : `claude/busy-blackburn-0ee195`

---

## 1. Contexte et problème

ProbaLab existe en production avec un moteur de probabilités sportives mature : Dixon-Coles + ELO + ensemble XGBoost calibré + analyses narratives Gemini, alimentant 8 ligues foot et la NHL. Backend FastAPI + frontend React 19 + Supabase + Stripe + déploiement Vercel/Railway. ~381 tests, suite ML opérationnelle.

**Le problème n'est pas le moteur, c'est le produit autour.** Plusieurs itérations ont fragmenté l'identité (value betting → spécialiste probas → sport intelligence dashboard), le frontend cumule des couches de pivots successifs, et le positionnement n'est pas assez clair pour convertir des visiteurs grand public en abonnés payants.

**Décision owner** : on garde le moteur ML et le backend FastAPI. On refait **toute l'expérience produit from scratch** : positionnement, frontend, paywall, onboarding, monétisation. Nouveau dossier `web/` construit en parallèle de `dashboard/` actuel, switch DNS au cutover.

## 2. Objectifs

1. **Positionnement clair** : "Comprends puis parie." Plateforme hybride encyclopédie probabiliste + tipster, foot + NHL, pour parieurs débutants et intermédiaires.
2. **Conversion freemium maximale** : free généreux pour acquisition + SEO, paywall placé sur la profondeur d'analyse pour conversion friction-optimale.
3. **Rétention quotidienne** : picks du jour + tracker bankroll perso + notif quotidienne créent un retour réflexe.
4. **SEO massif** : pages match individuelles indexables + pages guide pillar pour capter la longue traîne probabiliste sans concurrencer les médias sport généralistes.
5. **Stack moderne et polish élevé** : design Linear/Vercel/Stripe, dark mode soigné, animations Framer Motion, mobile-first.

## 3. Non-goals (scope explicitement exclu)

- Pas de refonte du moteur ML (Dixon-Coles + ELO + XGBoost + Gemini conservés tels quels).
- Pas de nouveau sport en V1 (foot + NHL uniquement).
- Pas d'app mobile native en V1 (web responsive PWA-ready, app native = V3 si traction).
- Pas d'alertes value bet temps réel en V1 (V2).
- Pas d'OCR scan de tickets en V1 (V3 si demande).
- Pas de programme parrainage en V1 (V2).
- Pas de multi-langue en V1 (FR uniquement, V3 pour EN).
- Pas de refactor backend autre qu'ajout d'endpoints nouveaux (`/api/v2/...`) et adaptation des endpoints existants.
- Pas de migration de schéma destructive (uniquement ajouts de tables et de colonnes).

## 4. Décisions de design (validées au brainstorming)

| # | Décision | Rationale |
|---|---|---|
| D1 | Cible : parieurs débutants et intermédiaires (pas pros) | Marché grand public, volume payant ; les pros vont sur Pinnacle/Trademate. |
| D2 | Promesse hybride "Comprends puis parie" : picks comme aimant + analyses comme valeur | Maximise les deux personas en un produit. Picks = hook addictif, analyses = valeur perçue. |
| D3 | Paywall sur la profondeur d'analyse (free généreux + premium spécialisé) | Free utile seul = SEO + bouche-à-oreille. Premium = niche (scores exacts, buteurs, IA narrative). Mur naturel au moment où l'user creuse. |
| D4 | Pricing 14,99 €/mois ou 9,99 €/mois en annuel (120 €/an = -33%) | Sweet spot français. Au-dessus de 10 € signale qualité, en-dessous de 20 € reste impulse buy. Annuel à -33% capture les convaincus. |
| D5 | Essai 7 jours **avec carte bancaire requise** | -50 % volume essai vs sans CB, mais x3 conversion finale. Filtre les tire-au-flanc, standard SaaS premium (Notion, Spotify Family). |
| D6 | Ton qualitatif premium mais accessible (référence Linear/Vercel/Stripe) | Cohérent avec cible débutant + intermédiaire. Pas Bloomberg, pas RotoWire. |
| D7 | Home = Hybride Hero (pick vedette + liste compacte des matchs du jour) | Combine hook (pick) + outil (matchs) en un seul écran. |
| D8 | Page match : free voit marchés mainstream, premium débloque les marchés profonds + analyses IA | Voir D14/D15 pour la liste exacte free vs premium par sport. |
| D9 | Navigation = Hub moderne (recherche centrale + tabs intention + sport switcher + filtres ligues) | Pattern Linear/Vercel/Notion. Scale si ajout de sports en V3. |
| D10 | Page Picks = onglets Safe/Value/Fun + cartes verticales avec contexte narratif | Mobile-first (70 % du trafic). Le contexte ("PSG enchaîne 5 victoires") transforme un chiffre en confiance pour le débutant. |
| D11 | Page Performance = 2 niveaux (ROI hero + courbe + breakdown / historique pick par pick paginé) | Crédibilité = transparence vérifiable. Sans liste pick par pick, le ROI n'a pas de valeur. |
| D12 | Tracker bankroll perso = manuel + import 1-clic depuis nos picks (premium uniquement) | Sweet spot ROI dev/valeur. Anti-churn killer (plus de paris saisis = plus de perte en partant). |
| D13 | Onboarding soft : 1 question (sports préférés) + tooltips contextuels au scroll/clic | Capture l'info essentielle sans friction. Tooltips activent les 3 features clés (sauvegarde, notif quotidienne, essai premium). |
| D14 | Marchés foot **free** : 1X2, BTTS Oui/Non, Plus/Moins de 2.5 buts, Double Chance | Marchés mainstream que le débutant connaît. |
| D15 | Marchés foot **premium** : variantes O/U (0.5, 1.5, 3.5, 4.5), scores exacts top 5, buteurs probables, handicaps asiatiques, corners, mi-temps/fin-de-match, BTTS combinés | Niche / profondeur, ce que le bettor veut creuser. |
| D16 | Marchés NHL **free** : Moneyline (1N2), Total O/U 5.5, Puck Line ±1.5 | 3 marchés mainstream pour parité avec le foot. |
| D17 | Marchés NHL **premium** : tous les player props (points 1+/2+, buts 1+, passes 1+, tirs 4+), score exact, écart final, période avec le plus de buts, totaux variantes (4.5, 6.5) | Player props = killer feature premium NHL (marché en explosion en Amérique du Nord). |
| D18 | SEO V1 = pages match indexables (~4000/an) + 5 pages guide pillar | Stratégie longue traîne probabiliste (Sofascore-like) + autorité (Investopedia-like). |
| D19 | Stack frontend = nouveau dossier `web/` en parallèle, switch DNS au cutover | Clean slate sans casser la prod. Réutilise le code qui marche par copie ciblée (auth, types Supabase). |
| D20 | Stack technique : Vite + React 19 + TS + Tailwind 4 + shadcn + Radix + Framer Motion + react-query + Recharts + Supabase JS + Stripe.js | Stack identique à `dashboard/` actuel (déjà éprouvé) mais sans dette. |
| D21 | Auth = Supabase email/password + Google OAuth en V1 | Google OAuth +30 % conversion signup, no-brainer ROI. |
| D22 | Notifs : email quotidien 7h45 (free + premium) + Telegram premium-only | Email = baseline rétention. Telegram = hook premium fort, anti-churn. |
| D23 | Métriques de succès V1 mesurées 30/60 jours post-launch (voir §13) | Critères go/no-go pour décider scope V2. |

## 5. Architecture des pages

```
/                                  → Home hybride hero (visiteur + connecté)
/auth/signup                       → Signup email + Google OAuth
/auth/login                        → Login
/auth/callback                     → OAuth callback handler
/onboarding                        → 1 question sports + tooltips déclenchés sur /picks
/picks                             → Picks du jour (onglets Safe/Value/Fun)
/performance                       → Niveau 1 : ROI hero + courbe + breakdown
/performance/historique            → Niveau 2 : pick par pick paginé
/foot/<slug-match>                 → Page match foot (free + premium gating)
/foot/ligue/<slug-ligue>           → Liste matchs d'une ligue (SEO)
/nhl/<slug-match>                  → Page match NHL (free + premium gating)
/bankroll                          → Tracker perso (premium uniquement)
/guides/comprendre-probas-foot     → Pillar SEO 1
/guides/btts-explique              → Pillar SEO 2
/guides/over-under-explique        → Pillar SEO 3
/guides/value-betting-debutants    → Pillar SEO 4
/guides/kelly-criterion            → Pillar SEO 5
/compte                            → Mon compte (overview)
/compte/abonnement                 → Lien vers Stripe Customer Portal
/legal/mentions                    → Mentions légales
/legal/cgu                         → CGU
/legal/cookies                     → Politique cookies
/legal/jeu-responsable             → Page obligatoire jeu responsable (lien ANJ)
/404, /500                         → Pages erreur
```

## 6. Architecture frontend (`web/`)

```
web/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── playwright.config.ts
├── vitest.config.ts
├── public/
│   ├── robots.txt
│   ├── favicon, og-images, apple-touch-icon
│   └── (sitemaps servis par FastAPI, pas en static)
├── src/
│   ├── main.tsx
│   ├── App.tsx                   → router + QueryClient + AuthProvider + SubscriptionProvider
│   ├── lib/
│   │   ├── supabase.ts           → client Supabase (auth uniquement, pas de queries DB côté front)
│   │   ├── api.ts                → fetch wrapper authentifié + react-query hooks
│   │   ├── stripe.ts             → @stripe/stripe-js init
│   │   ├── analytics.ts          → tracking events (PostHog ou Plausible self-hosted)
│   │   ├── cn.ts                 → clsx + tailwind-merge
│   │   ├── seo.ts                → helpers JSON-LD (SportsEvent, Article, BreadcrumbList)
│   │   └── format.ts             → format date/cote/proba/montant
│   ├── components/
│   │   ├── ui/                   → shadcn primitives (button, card, dialog, tabs, tooltip, sheet, dropdown, input, select, skeleton, toast)
│   │   ├── layout/
│   │   │   ├── AppShell.tsx      → header + content + footer
│   │   │   ├── Header.tsx        → logo + recherche + tabs + sport switcher + user menu
│   │   │   ├── MobileNav.tsx     → bottom tabs mobile
│   │   │   └── Footer.tsx
│   │   ├── match/
│   │   │   ├── MatchCard.tsx     → carte match dans une liste
│   │   │   ├── MatchHeader.tsx   → bandeau haut de page match
│   │   │   ├── ProbaBar.tsx      → barre 3 zones colorées (1X2 / Moneyline)
│   │   │   ├── MarketGrid.tsx    → grille de marchés
│   │   │   ├── MarketCard.tsx    → 1 marché (free ou locked)
│   │   │   ├── AnalysisBlock.tsx → bloc analyse IA narrative (premium)
│   │   │   └── FormStrip.tsx     → forme 5 derniers matchs
│   │   ├── picks/
│   │   │   ├── PicksTabs.tsx     → onglets Safe/Value/Fun + compteurs
│   │   │   ├── PickCard.tsx      → grande carte verticale avec contexte
│   │   │   └── PickResolutionBadge.tsx → ✓/✗ pour picks résolus
│   │   ├── performance/
│   │   │   ├── ROIHero.tsx       → bloc gradient avec ROI principal
│   │   │   ├── ProfitCurve.tsx   → Recharts area chart
│   │   │   ├── PeriodSelector.tsx → 7j / 30j / 90j / all
│   │   │   ├── CategoryBreakdown.tsx
│   │   │   └── PickHistoryTable.tsx → table paginée pick par pick
│   │   ├── bankroll/
│   │   │   ├── BankrollDashboard.tsx
│   │   │   ├── AddBetForm.tsx    → modal saisie manuelle
│   │   │   ├── BetsTable.tsx
│   │   │   ├── ImportFromPickButton.tsx
│   │   │   └── BankrollStats.tsx
│   │   ├── paywall/
│   │   │   ├── PremiumLockCard.tsx → carte locked avec CTA
│   │   │   ├── PremiumGate.tsx   → wrapper conditionnel
│   │   │   ├── UpgradeModal.tsx  → modal full d'upgrade (déclenché par CTA)
│   │   │   └── TrialBanner.tsx   → bandeau "Essai 7j gratuits"
│   │   ├── onboarding/
│   │   │   ├── SportsQuestion.tsx → modal 1 question
│   │   │   └── ContextualTooltip.tsx → tooltip déclenché au scroll/clic
│   │   ├── seo/
│   │   │   ├── MatchPageSchema.tsx  → JSON-LD SportsEvent
│   │   │   ├── BreadcrumbsJSONLD.tsx
│   │   │   ├── ArticleJSONLD.tsx    → pages guide
│   │   │   └── GuidePageLayout.tsx  → layout standardisé pages guide
│   │   └── shared/
│   │       ├── ErrorBoundary.tsx    → racine app (leçon 79)
│   │       ├── LoadingSpinner.tsx
│   │       └── EmptyState.tsx
│   ├── pages/                    → 1 fichier par route (HomePage, MatchPage, PicksPage, etc.)
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useSubscription.ts    → { isPremium, status, trialEndsAt }
│   │   ├── useMatches.ts         → liste matchs du jour
│   │   ├── useMatch.ts           → 1 match avec marchés
│   │   ├── usePicks.ts
│   │   ├── usePerformance.ts
│   │   ├── usePickHistory.ts     → pagination
│   │   ├── useBankroll.ts
│   │   └── useUserPreferences.ts
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   └── SubscriptionContext.tsx
│   ├── types/
│   │   ├── supabase.ts           → types générés via supabase gen types
│   │   ├── api.ts                → types des payloads API V2
│   │   └── domain.ts             → types métier (Match, Pick, Market, etc.)
│   └── styles/
│       └── globals.css           → directives Tailwind + design tokens en CSS vars
├── tests/
│   ├── unit/                     → tests Vitest des composants pure-fonction
│   └── components/               → tests Testing Library
└── e2e/
    ├── auth-signup.spec.ts
    ├── match-paywall-free.spec.ts
    ├── match-paywall-premium.spec.ts
    ├── checkout-flow.spec.ts
    ├── onboarding.spec.ts
    └── bankroll-import.spec.ts
```

## 7. Architecture backend (endpoints à ajouter ou adapter)

L'existant `api/main.py`, `api/routers/*` est conservé. Nouveaux endpoints sous le préfixe `/api/v2/` (déjà partiellement utilisé) :

```
GET  /api/v2/home
     → { featured_pick, today_matches: [{ league, matches: [...] }], live_picks_count }

GET  /api/v2/picks?date=YYYY-MM-DD&category=safe|value|fun&sport=foot|nhl
     → { picks: [{ id, sport, market, selection, probability, odds, context, is_premium, ... }] }

GET  /api/v2/match/<fixture_id>
     → {
         match: { ... },
         markets: [
           { name: "1X2", is_premium: false, data: {...} },
           { name: "exact_score", is_premium: true, data: {...} | null },
           ...
         ],
         analysis: { is_premium: true, content: "..." | null },
         form_home, form_away, h2h, lineups, weather
       }

GET  /api/v2/performance?period=7d|30d|90d|all&category=all|safe|value|fun
     → { roi, win_rate, profit, total_picks, curve: [{ date, profit }], breakdown_by_category }

GET  /api/v2/performance/picks?page=1&page_size=50&filter=...
     → { picks: [...], total, page, page_size }

POST /api/v2/onboarding
     body: { sports: ["foot","nhl"], level: "debutant" }

PATCH /api/v2/notifications/preferences
     body: { email_daily_pick, telegram_enabled }

POST /api/v2/notifications/telegram/connect
     → retourne un lien deep-link bot Telegram avec token

# Bankroll perso (premium only, middleware require_premium)
POST /api/v2/bankroll/bets
GET  /api/v2/bankroll/bets?status=...&page=...
PATCH /api/v2/bankroll/bets/<id>
DELETE /api/v2/bankroll/bets/<id>
POST /api/v2/bankroll/import-from-pick   body: { pick_id, stake }
GET  /api/v2/bankroll/stats?period=...

# Stripe
POST /api/stripe/checkout-session
     body: { plan: "monthly"|"annual" }
     → { url } (redirect Stripe Checkout)
POST /api/stripe/customer-portal
     → { url } (redirect Stripe Customer Portal)
POST /api/stripe/webhook
     (existe déjà — étendre pour gérer customer.subscription.trial_will_end, .updated, .deleted, .created)

# SEO
GET  /sitemap-foot.xml             → généré dynamiquement, cache 1h
GET  /sitemap-nhl.xml              → idem
GET  /sitemap-guides.xml           → 5 URLs statiques
GET  /robots.txt                   → liste les sitemaps
```

**Middleware `require_premium`** : décorateur FastAPI qui vérifie `user_subscriptions.status IN ('trialing', 'active')`. Renvoie 402 (Payment Required) si pas premium, gérée côté front comme une redirection vers `/compte/abonnement`.

## 8. Schéma DB — tables nouvelles

Toutes les nouvelles tables ont **RLS strict** : `service_role` peut tout, l'utilisateur peut lire/écrire **uniquement ses propres rows**.

```sql
-- 8.1 Préférences user (onboarding + notifications)
create table user_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  sports text[] not null default '{}',                -- ['foot','nhl']
  level text default 'debutant' check (level in ('debutant','intermediaire')),
  email_daily_pick boolean not null default true,
  telegram_enabled boolean not null default false,
  telegram_chat_id text,
  telegram_connect_token text,                        -- token unique pour le deep-link
  telegram_connect_token_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_user_prefs_telegram_chat on user_preferences(telegram_chat_id) where telegram_chat_id is not null;

alter table user_preferences enable row level security;
create policy "user_self_read_prefs"  on user_preferences for select using (auth.uid() = user_id);
create policy "user_self_write_prefs" on user_preferences for all    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_all_prefs" on user_preferences for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- 8.2 Bankroll perso (paris saisis ou importés depuis nos picks, premium only)
create table user_bets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source text not null check (source in ('manual','imported_from_pick')),
  pick_id uuid,                                       -- FK vers best_bets.id si importé (sans contrainte hard pour permettre l'évolution)
  fixture_id text,
  sport text not null check (sport in ('football','nhl')),
  market text not null,                               -- ex: "1X2", "OU2.5", "PLAYER_POINTS_1+_McDavid"
  selection text not null,                            -- ex: "PSG", "OVER", "YES"
  stake numeric(10,2) not null check (stake > 0),
  odds numeric(10,3) not null check (odds > 1),
  status text not null default 'pending' check (status in ('pending','won','lost','void')),
  payout numeric(10,2),                               -- = stake * odds si won, 0 si lost, stake si void
  notes text,
  bet_date timestamptz not null default now(),
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);

create index idx_user_bets_user_date on user_bets(user_id, bet_date desc);
create index idx_user_bets_status on user_bets(user_id, status);
create index idx_user_bets_pick on user_bets(pick_id) where pick_id is not null;

alter table user_bets enable row level security;
create policy "user_self_read_bets"  on user_bets for select using (auth.uid() = user_id);
create policy "user_self_write_bets" on user_bets for all    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "service_role_all_bets" on user_bets for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');

-- 8.3 Subscriptions Stripe (source de vérité premium gating)
create table user_subscriptions (
  user_id uuid primary key references auth.users(id) on delete cascade,
  stripe_customer_id text unique not null,
  stripe_subscription_id text unique,
  status text not null check (status in ('trialing','active','past_due','canceled','incomplete','incomplete_expired','unpaid')),
  plan text check (plan in ('monthly','annual')),
  trial_ends_at timestamptz,
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  canceled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_user_subs_status on user_subscriptions(status);
create index idx_user_subs_stripe_cust on user_subscriptions(stripe_customer_id);

alter table user_subscriptions enable row level security;
create policy "user_self_read_subs"  on user_subscriptions for select using (auth.uid() = user_id);
create policy "service_role_all_subs" on user_subscriptions for all using (auth.role() = 'service_role') with check (auth.role() = 'service_role');
-- Pas de policy d'écriture pour l'user : seul le webhook Stripe (service_role) écrit ici.
```

**Note migrations** : ces tables s'ajoutent aux existantes. Elles n'altèrent rien. Les migrations vont dans `ProbaLab/supabase/migrations/` au format daté (`<timestamp>_v2_relaunch_*.sql`).

## 9. Logique de premium gating

**Source unique de vérité** : la table `user_subscriptions`. Champ : `status IN ('trialing', 'active')` ⇒ premium actif.

### Frontend

- Hook `useSubscription()` : retourne `{ isPremium: boolean, status, trialEndsAt, planType }`.
- Composant `<PremiumGate>` :
  ```tsx
  <PremiumGate fallback={<PremiumLockCard market="exact_score" />}>
    <ExactScoreTable data={...} />
  </PremiumGate>
  ```
- Pour les marchés, le backend renvoie le payload avec un flag `is_premium` par marché. Si `is_premium && !user.isPremium`, le frontend remplace le `data` par un `<PremiumLockCard>` (état flouté + CTA).
- `<TrialBanner>` affiché en haut si `status === 'trialing'` avec compte à rebours ("J-3 d'essai").
- `<UpgradeModal>` déclenchée par tout CTA "Débloquer" avec deep-link sur `/compte/abonnement` qui appelle `/api/stripe/checkout-session`.

### Backend

- Décorateur `@require_premium` (à créer dans `api/middleware/`) qui :
  1. Récupère `user_id` via le JWT Supabase déjà parsé.
  2. Query `user_subscriptions` : retourne 402 si pas dans `('trialing','active')`.
  3. Sinon laisse passer.
- Endpoints couverts : `/api/v2/bankroll/*`, `/api/v2/match/<id>` renvoie tous les marchés mais avec `data: null` pour ceux flagués `is_premium=true` si l'user n'est pas premium (gating au niveau du payload pour pouvoir teaser proprement).
- Endpoint `/api/v2/picks` : renvoie tous les picks mais avec `is_premium=true` flag, et le frontend cache les détails (selection / odds / probability) si `is_premium && !user.isPremium`.

## 10. Stratégie SEO

### 10.1 Pages match indexables

**URL** : `/foot/<home-slug>-vs-<away-slug>-<yyyy-mm-dd>` (ex: `/foot/psg-vs-lyon-2026-05-12`).

**Pré-rendu** : Vite SSG ou Vercel ISR (à trancher dans le plan d'implémentation — voir §15). Le contenu doit être servi en HTML pré-rendu pour Google.

**Contenu visible non-connecté** :
- H1 : "PSG vs Lyon — Probas et analyse Ligue 1, 12 mai 2026"
- Probas free (1X2, BTTS, O/U 2.5, DC) avec barres visuelles + libellés écrits
- Forme 5 derniers matchs des 2 équipes (résumé textuel + visual)
- Classement actuel + position + écart points avec leader/qualif
- H2H 5 derniers face-à-face (résumé textuel)
- Compositions probables (si dispo)
- Section "Marchés Premium" teasée avec lock + CTA "Inscription gratuite"
- 5 liens internes : 3 autres matchs du jour, 1 page ligue, 1 page guide pertinente

**JSON-LD** : `SportsEvent` schema pour rich snippets Google.

**Sitemap** : `/sitemap-foot.xml` et `/sitemap-nhl.xml` générés par FastAPI, mis en cache 1h, listant uniquement les matchs des 30 derniers jours et 30 prochains jours (limite Google ~50k URLs/sitemap).

### 10.2 Pages guide pillar

5 pages écrites une fois, mises à jour 2x/an :

1. `/guides/comprendre-probas-foot` — pédagogique, ~1500 mots, cible "comment lire probas pari foot", "probabilité paris sportifs"
2. `/guides/btts-explique` — cible "BTTS pari", "les deux équipes marquent expliqué"
3. `/guides/over-under-explique` — cible "over under foot", "plus ou moins de buts"
4. `/guides/value-betting-debutants` — cible "value bet pari", "qu'est-ce qu'un value bet"
5. `/guides/kelly-criterion` — cible "Kelly Criterion", "calcul mise optimale"

Layout standardisé : H1, sommaire ancré, sections H2/H3, exemples chiffrés, CTA discret en bas vers ProbaLab.

### 10.3 Indexation rate-limit

Éviter de submit 4000 URLs d'un coup à Google → drip-feed via Search Console (50/jour pendant les 2 premiers mois). Le sitemap n'expose que les matchs récents pour ne pas confondre Google sur l'historique.

## 11. Onboarding flow détaillé

```
Signup (email/pwd ou Google OAuth)
  ↓ (callback OAuth ou email confirmé)
Modal sur /onboarding (impossible à skipper) :
  "Quels sports te plaisent ?"
  [⚽ Foot] [🏒 NHL] [Les deux]
  → POST /api/v2/onboarding
  ↓
Redirect vers /picks?welcome=1 (page picks personnalisée selon sports choisis)
  ↓
Tooltip 1 (apparait après 2s) :
  "💡 Sauvegarde tes picks favoris en cliquant sur l'étoile"
  ↓
Tooltip 2 (au 1er clic sur un pick) :
  "📩 Reçois la sélection chaque matin à 7h45"
  [Activer la notif email] (1 clic = activation)
  ↓
Tooltip 3 (quand l'user atteint le bottom de la page) :
  "🎯 Essaie Premium gratuitement 7 jours"
  [En savoir plus] → modal upgrade
```

Les 3 tooltips sont stockés en localStorage avec un flag "vu" pour ne pas se répéter. Visibles uniquement les 7 premiers jours du compte.

## 12. Plan de cutover

```
Semaine 1   → Setup web/, design system, auth Supabase, 3 pages prototype (home, match, login).
Semaine 2-3 → Pages publiques complètes (home, match, picks, performance niveaux 1-2),
              composants ui/ shadcn complétés.
Semaine 4   → Stripe checkout + customer portal + webhook + premium gating end-to-end + onboarding.
Semaine 5   → Tracker bankroll perso + endpoints backend correspondants + import 1-clic.
Semaine 6   → Pages SEO match individuelles + 5 guides pillar + sitemaps + JSON-LD.
Semaine 6.5 → QA complète : Playwright e2e + load test + a11y axe + Lighthouse > 90 sur toutes les pages.
              Preview deploy Vercel sur web-staging.probalab.fr pour 48h de tests internes.

Cutover J0  : switch Vercel domain :
              probalab.fr → web/ (nouveau déploiement)
              dashboard/ déplacé vers legacy.probalab.fr (gardé 15j en sécurité)
              redirection 301 des anciennes URLs critiques vers les nouvelles.

Cutover J+1-7 : monitoring intensif (Vercel logs, Sentry, GA4),
                rollback DNS prêt en <30s si crise.

J+15        : suppression définitive de dashboard/ et legacy.probalab.fr après confirmation 0 incident.
```

## 13. Métriques de succès V1 (mesurées 30/60 jours post-launch)

| Métrique | Cible | Mesure |
|---|---|---|
| Signups free 30j | 1 000 | analytics |
| Activation J+7 (% users qui reviennent) | ≥ 40 % | analytics cohort |
| Conversion free → trial 30j | ≥ 8 % | Stripe |
| Conversion trial → paid | ≥ 50 % | Stripe (essai avec CB filtre les tire-au-flanc) |
| Churn mensuel | ≤ 8 % | Stripe |
| NPS | > 40 | survey in-app après J+14 |
| Pages indexées Google 60j | ≥ 500 | Search Console |
| Lighthouse Performance toutes pages | ≥ 90 | CI Lighthouse |
| Accessibilité axe-core | 0 erreur niveau A/AA | CI axe-core |

## 14. Sécurité et conformité

- **RLS strict** sur les 3 nouvelles tables (vérifié par tests d'intégration `pytest -m integration`).
- **Webhook Stripe** : vérification signature avec `STRIPE_WEBHOOK_SECRET`, idempotence sur `event.id`.
- **Token Telegram connect** : single-use, expiration 15 minutes.
- **Pas de secret en clair** : tout en variables d'environnement (Vercel + Railway).
- **Page jeu responsable** obligatoire (lien ANJ, message d'avertissement, lien aide-au-joueur 09 74 75 13 13).
- **Cookies** : bannière de consentement (analytics opt-in), stockage du choix.
- **CGU + Mentions légales + Politique cookies** à rédiger avant cutover (templates à adapter).
- **Vérification d'âge** : checkbox 18+ au signup (exigence ANJ pour les sites parlant de paris en France, même sans transaction directe).
- **Disclaimer** sur toutes les pages picks et match : "Les probabilités sont calculées par des modèles statistiques. Ne constituent pas un conseil financier. Pariez de manière responsable."

## 15. Questions ouvertes pour le plan d'implémentation

Ces questions sont à trancher au moment de la rédaction du plan (next step après ce spec) :

1. **Pré-rendu pages match** : Vite SSG (build complet) ou Vercel ISR avec revalidation incrémentale ? ISR plus adapté à 4000+ pages dynamiques mais coût Vercel à valider.
2. **Pré-rendu pages guide** : statique au build, simple.
3. **Format slug match** : confirmation `<home-slug>-vs-<away-slug>-<yyyy-mm-dd>`. Gestion des accents/équipes étrangères (ex: "Bayern vs Köln" → "bayern-vs-koln-2026-05-12").
4. **Analytics** : PostHog cloud, PostHog self-hosted, ou Plausible self-hosted ? PostHog cloud le plus rapide à brancher mais coût qui scale ; Plausible self-hosted RGPD-friendly mais infrastructure à maintenir.
5. **Sentry** : OK ou alternative ? Pour erreurs frontend + API.
6. **Plan Stripe précis** : 1 produit "ProbaLab Premium" avec 2 prix (`monthly_price_id`, `annual_price_id`) ou 2 produits séparés ? La doc Stripe pousse vers 1 produit + 2 prix.
7. **Telegram bot** : conserver le bot existant ou en créer un nouveau dédié au flux V2 ? Évaluer la migration des chat_id existants.
8. **Trigger.dev** : conservé pour les jobs longs, pas changé en V1.

## 16. Points de vigilance issus des leçons existantes

(Croisé avec `ProbaLab/tasks/lessons.md` et CLAUDE.md projet)

- **ErrorBoundary à la racine de `web/`** (leçon 79) — non négociable.
- **Contract test API ↔ frontend** (leçon 77) — chaque endpoint V2 doit avoir un contract test backend qui épingle la shape consommée par le frontend.
- **fixture_id typage strict** — partout, jamais de mélange int/str.
- **Timezones UTC partout** — le frontend convertit en local au moment de l'affichage uniquement.
- **RLS testée après chaque migration** — `pytest -m integration` doit valider que l'user A ne lit pas les rows de l'user B.
- **Pas de blocage sur Gemini** — quota et latence ; les analyses IA doivent dégrader gracieusement (placeholder textuel statique si Gemini timeout).
- **381 tests existants** — ne jamais merger sans tests verts (cf CI GitHub Actions existante).
- **TDD obligatoire sur tout fix de bug** — un test rouge avant le fix.
- **Sécurité endpoints admin** — `Depends(verify_internal_auth)` sur tout endpoint admin (existe déjà).

## 17. Évolutions V2/V3 (post-launch, hors scope)

V2 (M+3 → M+6) :
- Alertes value bet temps réel (push web + Telegram).
- Notifications push web/mobile (PWA).
- Analyses éditoriales humaines des gros matchs (top 10/semaine).
- Outils interactifs SEO : calculateur Kelly, convertisseur cotes, simulateur bankroll.
- Tickets combos personnalisés (l'user crée son combo à partir de nos picks).
- Export CSV bankroll perso.
- Programme parrainage (1 mois offert pour parrain et filleul).
- Telegram "lite" gratuit (1 pick/jour) pour booster acquisition virale.

V3 (M+9 → M+12) :
- App mobile native iOS/Android (React Native ou Expo, à trancher).
- Multi-langue EN.
- Sports additionnels (basket NBA, tennis ATP/WTA).
- OCR scan ticket Winamax/Betclic (si demande premium forte).

---

*Document validé. Next step : rédaction du plan d'implémentation détaillé via la skill `writing-plans`.*
