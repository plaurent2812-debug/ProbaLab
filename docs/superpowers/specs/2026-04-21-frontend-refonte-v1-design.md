# Frontend Refonte V1 — Design Spec

**Date** : 2026-04-21
**Auteur** : Pierre Laurent + Claude (brainstorming collaboratif)
**Statut** : Validé, prêt pour plan d'implémentation
**Périmètre** : Refonte UX/UI complète du frontend ProbaLab (dashboard SPA)

---

## 1. Contexte & motivation

ProbaLab pivote de "combos Safe/Fun/Jackpot" vers "probabilités calibrées + value bets ≥5%". Le frontend actuel (15 pages, centré sur les combos) reflète encore l'ancien pitch. Cette refonte aligne l'UX avec le nouveau positionnement tout en préparant la démonstration publique du CLV (H2-SS1 déjà déployé côté backend).

**Objectifs mesurables** :
- Parcours principal *liste → fiche → décision de pari* fluide en 3 clics max
- Taux de conversion trial → premium ≥ 15% (baseline à établir)
- Mobile-first : 70% du trafic attendu sur mobile, Lighthouse Performance > 85
- Démonstration publique du CLV vs Pinnacle comme différenciateur principal

**Hors scope V1** : Admin, Performance admin, CGU/Confidentialité (laissés inchangés, refonte prévue en SS2/SS3 quand la donnée CLV sera stabilisée).

---

## 2. Profil utilisateur cible

Public mixte 50/50 avec deux modes cohabitant :

- **Parieur débutant/occasionnel** : consomme le pronostic Safe quotidien, scanne les probas 1X2, ignore l'edge et le Kelly.
- **Parieur intermédiaire éduqué** : lit les value bets, compare les cotes entre books, utilise Kelly fractionnel, suit son ROI par marché.

Le design doit servir les deux sans basculement de mode — la hiérarchie visuelle fait le tri (signal principal visible par tous, détails techniques accessibles pour ceux qui les cherchent).

**Parcours utilisateur principal validé** :
> Arrivée sur Accueil → scan des matchs du jour → clic sur un match → lecture de la fiche détaillée → décision de pari (placé ailleurs sur un site de bookmaker) → retour éventuel pour suivre le résultat dans Bankroll.

---

## 3. Matrice d'accès (visiteur / free / trial / premium)

| Contenu | Visiteur | Free (connecté) | Trial 30j | Premium |
|---|---|---|---|---|
| Marketing / landing `/` | ✅ | — | — | — |
| Pronostic Safe du jour | ❌ | ✅ | ✅ | ✅ |
| Probas 1X2 sur tous matchs | Aperçu flouté | ✅ | ✅ | ✅ |
| Fiche match — stats, H2H, forme | Aperçu | ✅ | ✅ | ✅ |
| Value bets ≥5% | Teaser | Teaser (aperçu 1 value bet) | ✅ | ✅ |
| Probas complètes (BTTS, O/U, DC, score, buteurs) | ❌ | 1X2 uniquement | ✅ | ✅ |
| Analyse IA narrative (Gemini) | ❌ | 1er paragraphe flouté | ✅ | ✅ |
| Combo Fun quotidien | ❌ | ❌ | ✅ | ✅ |
| Bankroll tracker | ❌ | ❌ | ✅ | ✅ |
| Alertes personnalisées | ❌ | ❌ | ✅ | ✅ |
| Track record public (Premium page) | ✅ | ✅ | ✅ | ✅ |

**Règles de bascule** :
- Non-connecté → `/` marketing public avec preview flouté + CTA "Créer un compte gratuit"
- Inscription gratuite → accès immédiat à **Trial 30j full premium** (sans carte bancaire)
- Fin de trial sans abonnement → bascule en mode Free avec **révélation progressive** (aperçu partiel qui montre la qualité, pas un gating total)
- Abonnement Premium actif → tout débloqué en permanence

**Combos Safe/Fun/Jackpot** : Safe devient le pronostic free du jour (cote 1.8–2.2, pari simple ou combo 2 legs max). Fun devient un combo curated premium quotidien (cote 6–12). **Jackpot est supprimé**.

---

## 4. Architecture & routing

### Routes finales

| Route | Composant | Accès |
|---|---|---|
| `/` | `Home` | Public (landing) / connecté (dashboard) |
| `/matchs` | `Matches` | Public (preview) / connecté (complet) |
| `/matchs/:fixtureId` | `MatchDetail` | Public (preview) / connecté |
| `/login` | `Login` | Public |
| `/register` | `Register` | Public |
| `/compte` | `Account` (tabs : profil · abonnement · bankroll · notifications) | Connecté |
| `/premium` | `Pricing` | Public |
| `/admin` | `Admin` (inchangé V1) | Admin |
| `/performance` | `Performance` (inchangé V1) | Admin |
| `/cgu` `/confidentialite` | inchangés | Public |

### Suppressions

`/paris-du-soir`, `/watchlist`, `/nhl`, `/nhl/match/:id`, `/hero-showcase`, `/football`, `/football/match/:id` sont retirés. Le contenu migre :
- `/paris-du-soir` → value bets deviennent un **badge inline** sur chaque match de `/matchs` + une section de la fiche match
- `/watchlist` → absorbé dans `/compte` onglet **Bankroll**
- `/nhl`, `/football` → fusionnent dans `/matchs` avec **filtre sport** (chips `Tous · ⚽ Foot · 🏒 NHL`)
- `/hero-showcase` → supprimé (page de démo interne)

### Navigation

- **Mobile** : bottom nav 3 icônes (`Accueil · Matchs · Compte`), sticky bas.
- **Desktop** : header sticky top avec logo + nav horizontale (`Accueil · Matchs · Compte`) + badge état (`Free` / `Trial J-12` / `Premium`) + avatar à droite.
- **Trial banner** : bandeau sticky en haut de toutes les pages connectées, indique `Trial premium · J-X · Tout est débloqué jusqu'au [date]` avec lien "Activer l'abonnement" (visible uniquement pendant la trial).

---

## 5. Design system

### Identité visuelle validée : **Fintech / Trading**

Densité élevée, typographie numérique précise, palette émeraude sur fond nuit. Inspiration Bloomberg / Robinhood / Linear. Ton sérieux, data-driven.

### Palette (mode sombre par défaut, light disponible)

| Token | Dark | Light | Usage |
|---|---|---|---|
| `--bg` | `#0a0e1a` | `#fafaf8` | Fond page |
| `--surface` | `#111827` | `#ffffff` | Cards, rows |
| `--surface-2` | `#1f2937` | `#f4f4f1` | Hover, inputs |
| `--border` | `#1f2937` | `#e5e5e0` | Séparateurs |
| `--text` | `#e5e7eb` | `#0a0a0a` | Texte principal |
| `--text-muted` | `#94a3b8` | `#6b7280` | Texte secondaire |
| `--text-faint` | `#64748b` | `#9ca3af` | Labels, timestamps |
| `--primary` | `#10b981` | `#059669` | Actions, probas, gains |
| `--primary-soft` | `#064e3b` | `#d1fae5` | Fonds émeraude tamisés |
| `--value` | `#fbbf24` | `#d97706` | Value bet, premium, amber |
| `--danger` | `#ef4444` | `#dc2626` | Pertes, live, alertes |
| `--info` | `#60a5fa` | `#2563eb` | Liens, infos neutres |

### Typographie

- **Famille principale** : Inter (déjà chargée). Monospace tabulaire pour chiffres : `font-variant-numeric: tabular-nums`.
- **Famille chiffres hero** : Inter en display weight (700) + letter-spacing réduit.
- **Échelle** (rem base 16px) : 12px (labels), 14px (corps), 16px (principal), 18px (titres cards), 20–24px (titres sections), 28–44px (hero stats).
- **Poids** : 400 (texte), 500 (labels), 600 (titres), 700 (chiffres emphase).
- **Règle lisibilité stricte** (lesson 55) : jamais sous 12px. Infos critiques (edge, odds, probas) minimum 14px.

### Grille & espacement

- Grille 4px (toutes marges multiples de 4).
- Mobile : 1 colonne, gouttière 16px, marge page 16px.
- Desktop : max-width 1200px centré, gouttière 24px, marge page 32px.

### Composants système

- `<StatTile>` : label + valeur hero + delta (ex: `ROI · +12.4% · +0.8 vs 7j`).
- `<MatchRow>` : ligne compacte avec heure · équipes · barre proba 1X2 segmentée · chips (`★ SAFE` / `⚡ VALUE +7.2%`).
- `<ProbBar>` : barre 3 segments colorés selon proba dominante (`#10b981` pour le max, `#334155` et `#1f2937` pour les autres).
- `<ValueBadge>` : chip amber avec edge% affiché.
- `<OddsChip>` : chip mono tabulaire pour une cote (ex: `@1.92`).
- `<BookOddsRow>` : liste de bookmakers avec cote et highlight sur le meilleur prix.
- `<LockOverlay>` : cadenas + blur-sm sur zone premium (contenu partiellement visible).
- `<TrialBanner>` : bandeau top sticky pendant trial 30j.
- `<RuleChip>` : chips composables pour le rules builder des notifications.

### Iconographie & animation

- **Icônes** : Lucide (déjà en place). Pas d'emojis dans les composants système (ils restent dans le texte généré par Gemini si présents).
- **Transitions** : 150ms ease-out sur hover/click uniquement. Pas d'animations décoratives (cohérence ton fintech).
- **Chart library** : `recharts` (remplace Victory actuel) pour les courbes ROI/bankroll — léger, composable, bien typé.

---

## 6. Page Accueil (`/`)

### Objectif principal
Convertir visiteur → free, free → premium. Le Safe du jour est le premier contact pour un user connecté.

### Structure (ordre validé : A)

#### Non-connecté (landing marketing)
1. Hero sobre — titre fort ("Parier avec une vraie probabilité, pas un feeling"), sous-titre positionnement CLV, CTA "Essai gratuit 30 jours".
2. Preview floutée des matchs du jour (3 matchs visibles avec blur sur les probas, chip "Créer un compte pour voir").
3. Section track record public (mêmes KPIs que page Premium mais en teaser condensé).
4. Lien vers `/premium` pour détails.

#### Connecté (dashboard)
1. Trial banner sticky (si trial active).
2. Header compact avec date, badge statut, avatar.
3. **Stats strip 4 KPIs** : `ROI 30J` · `Accuracy` · `Brier 7J` · `Bankroll` (tile-val 22–26px, couleur primary si positif, danger si négatif).
4. **Safe du jour** — card gradient émeraude (`linear-gradient(135deg, #064e3b 0%, #0f172a 70%)`), border-left 3px `#10b981` :
   - Label `★ SAFE · PRONOSTIC DU JOUR` + chip `FREE`
   - Titre du pari (ex : `PSG gagne vs Lens`)
   - Cote hero 32px + probabilité
   - Barre de proba 4px
   - Justification textuelle 2–3 lignes (tirée du modèle/analyse)
5. **Matchs du soir** (liste complète de la journée) :
   - Filtre sport chips (`Tous · ⚽ Foot · 🏒 NHL`)
   - Liste groupée par ligue avec en-tête coloré
   - Chaque ligne : heure · équipes · barre proba + chiffres · chips signaux (`★ SAFE`, `⚡ VALUE +7.2%`)
6. **Colonne droite desktop sticky** (mobile : inline après matchs) :
   - Safe du jour (déjà présent en col gauche mobile, en sticky droite desktop)
   - Value bets premium (2 lignes compactes edge/Kelly)
   - CTA conversion premium (card amber sobre, message post-trial)

### Endpoints consommés
- `GET /api/predictions?date=today` — liste matchs + probas
- `GET /api/best-bets?date=today&sport=football,nhl` — value bets
- `GET /api/performance/summary?window=30` — KPIs strip
- `GET /api/safe-pick?date=today` — pronostic Safe du jour (nouveau endpoint à créer)
- `GET /api/user/bankroll/summary` — bankroll tile (connecté)

---

## 7. Page Matchs (`/matchs`)

### Objectif
Permettre à l'user de parcourir tous les matchs du jour/semaine et filtrer précisément.

### Structure

#### Mobile
1. Header compact + bouton filtres secondaires.
2. Sport tabs chips (`Tous · ⚽ Foot · 🏒 NHL`) avec compteurs.
3. Date scroller horizontal (hier → +5 jours), `AUJOURD'HUI` actif en émeraude.
4. Toggle `⚡ Value only` pour filtrer rapidement.
5. Liste **groupée par ligue** avec en-tête coloré (L1 bleu, PL violet, SA vert, BL rouge, La Liga orange, UCL bleu clair, UEL orange, NHL gris).
6. Chaque match : heure · équipes · barre proba + chiffres · chips signaux inline.
7. Click → fiche match.

#### Desktop
1. Header + date scroller élargi avec flèches ‹ ›.
2. **Sidebar filtres persistante** (220px) :
   - Sport (checkboxes avec compteurs)
   - Ligue (checkboxes avec compteurs par ligue active)
   - Signaux (`⚡ Value bet ≥5%`, `★ Safe du jour`, `Confiance élevée`)
   - Tri (dropdown : heure / edge / confiance / ligue)
3. **Table dense par ligue** :
   - Colonnes : `Heure · Match · Barre probas + chiffres · Signal · Meilleure cote + book · Détail →`
   - Chaque ligue dans une card groupée avec en-tête
   - Ligne value bet highlight léger avec accent amber

### Endpoints
- `GET /api/matches?date=YYYY-MM-DD&sports=foot,nhl&leagues=...&signals=value,safe` — nouveau endpoint consolidé
- `GET /api/matches/best-odds?fixtureIds=...` — meilleures cotes par match (déjà partiellement dispo via best-bets)

---

## 8. Page Fiche match (`/matchs/:fixtureId`)

### Objectif
Donner toutes les infos pour prendre une décision de pari en un seul écran, reco principale toujours visible (desktop sticky).

### Structure

#### Desktop (2 colonnes)
**Header partagé** : breadcrumb + match hero (logos 64px, date/heure/stade centrés, forme V-V-N-V-V colorée par équipe, classement).

**Colonne gauche (scrollable)** :
1. **Stats comparatives 5 derniers matchs** : xG, buts encaissés, possession — barres bicolores comparatives.
2. **Historique H2H** : barre empilée (7V / 2N / 1V) + liste des 3 derniers affrontements.
3. **Analyse IA (Gemini)** : paragraphes narratifs avec emphasis typographiques (gras émeraude pour le signal positif, callout amber pour les warnings type "rotation UCL", callout émeraude final pour la reco rationnelle).
4. **Compositions probables** : formation + XI par équipe.
5. **Tous les marchés** (14 dispo) : grid 2 colonnes avec chaque ligne `marché · proba · cote`, value bets highlighted amber.

**Colonne droite sticky** (`position: sticky; top: 20px`) :
1. **Reco principale** : card gradient émeraude, pari recommandé, cote hero 34px, breakdown `CONFIANCE / KELLY / EDGE`, **tableau des 5 books** avec meilleur prix highlight émeraude.
2. **Probas 1X2** : 3 barres avec %.
3. **Value bets** (2–3 items) : edge + Kelly + meilleur book.
4. **Actions** : bouton `➕ Suivre dans mon bankroll` (primary), bouton `🔔 Alerte kick-off` (secondary).

#### Mobile (ordre décision rapide)
1. Back button + breadcrumb ligue
2. Match hero compact
3. **Notre recommandation** (gros bloc)
4. Probas 1X2
5. Value bets
6. Stats clés (forme récente)
7. Analyse IA
8. Tous les marchés

### Endpoints
- `GET /api/predictions/:fixtureId` — probas + stats + H2H + compositions
- `GET /api/best-bets/by-fixture/:fixtureId` — value bets du match
- `GET /api/odds/:fixtureId/comparison` — comparateur de cotes par book
- `GET /api/analysis/:fixtureId` — analyse IA Gemini (premium)
- `POST /api/user/bets` — ajouter au bankroll

### Gating free (post-trial)

- Value bets : 1 value bet visible en aperçu partiel (cotes floutées sauf la première), 2+ bloqués avec `LockOverlay` + message `Débloque tous les value bets avec Premium`.
- Analyse IA : 1er paragraphe visible, reste flouté avec `Débloque l'analyse complète avec Premium`.
- Tous les marchés : 1X2 visible, BTTS/O/U/Score/Buteurs tous floutés.

---

## 9. Page Premium (`/premium`)

### Objectif
Convertir vers trial 30j via la **preuve par la transparence**. Geste différenciant : track record LIVE vs Pinnacle, mis à jour toutes les 15 min.

### Structure (single-page, scroll vertical)

1. **Hero**
   - Label `PROBALAB PREMIUM` (émeraude)
   - Titre H1 44px : "Parier avec une vraie probabilité, pas un feeling."
   - Sous-titre : positionnement CLV ("Le seul pronostiqueur français qui publie son CLV vs Pinnacle en temps réel")
   - CTA primary `Essai gratuit 30 jours →` + CTA secondary `Voir le track record live ↓`
   - Mention `Sans engagement · Résiliation en 1 clic · Aucune carte requise pour la trial`

2. **Track record LIVE** (killer feature)
   - Label avec dot pulsing `LIVE · dernière MAJ il y a 4 min`
   - Titre "La preuve, pas les promesses."
   - 4 StatTiles grands format : `CLV vs Pinnacle 30j`, `ROI 90j`, `Brier 30j`, `Safe du jour 90j`
   - Courbe ROI cumulée 90 derniers jours (SVG line chart émeraude avec gradient area fill)
   - Toggle period 90j / 180j / 1an
   - Note bas : `Toutes les métriques calculées automatiquement sur l'intégralité des paris recommandés, sans cherry-picking. Source : github.com/probalab/track-record (dump JSON quotidien auditable).`

3. **Pricing side-by-side**
   - Titre "Un seul plan. Annule quand tu veux."
   - Card Free (0€ / pour toujours) : Safe quotidien, probas 1X2, track record
   - Card Premium (14,99€/mois) : border émeraude, badge `RECOMMANDÉ` amber, `🎁 30 jours d'essai · sans carte bancaire`, liste exhaustive features

4. **Garantie transparence** : `🛡️ Si notre CLV tombe sous 0% sur 30 jours glissants, on t'offre le mois. Publié en temps réel sur cette page.`

5. **FAQ courte** : 3 questions qui éduquent sur le CLV et rassurent sur la résiliation.

### Endpoints
- `GET /api/public/track-record/live` — nouveau endpoint public, retourne `{clv_30d, roi_90d, brier_30d, safe_rate_90d, roi_curve_90d: [...]}` (cache 5 min)

---

## 10. Page Compte (`/compte`)

### Structure : 4 tabs horizontaux

1. **Profil** : email, pseudo, avatar, mot de passe, suppression compte (RGPD).
2. **Abonnement** : statut actuel, prochain renouvellement, historique factures Stripe, résiliation 1 clic.
3. **Bankroll** : voir section 11 ci-dessous.
4. **Notifications** : voir section 12 ci-dessous.

---

## 11. Sous-page Bankroll (onglet Compte)

### Objectif
Tracker P&L personnel, remplace la Watchlist. Geste différenciant : **ROI par marché en barres** (visualisation actionnable).

### Structure

1. **Header section** : titre + `⚙ Paramètres bankroll` + `+ Ajouter un pari`
2. **5 KPIs strip** : `Bankroll` · `ROI 30J` · `Win Rate` · `Drawdown` · `Kelly actif`
3. **2 colonnes** :
   - Gauche : **Courbe évolution bankroll** 90j (toggle 7/30/90/All) avec highlight valeur actuelle
   - Droite : **ROI par marché** en barres horizontales (1X2, O/U, BTTS, DC, Score) — positif vert, négatif rouge
4. **Liste derniers paris** :
   - Filtres chips : Tous · En cours · Gagnés · Perdus
   - Colonnes : Date · Pari · Type (1X2/Over/BTTS…) · Cote · Mise · Résultat (chip WIN/LOSS/PENDING)
5. **Paramètres bankroll** (modal) : stake initial, Kelly fraction (0.1 / 0.25 / 0.5), plafond mise (% bankroll), reset

### Endpoints
- `GET /api/user/bankroll` — summary + paris
- `POST /api/user/bets` — ajout pari (depuis fiche match ou manuel)
- `PATCH /api/user/bets/:id` — maj résultat
- `GET /api/user/bankroll/roi-by-market` — breakdown ROI par marché
- `PUT /api/user/bankroll/settings` — paramètres Kelly / stake

---

## 12. Sous-page Notifications (onglet Compte)

### Objectif
Geste différenciant : **rules builder personnalisé** type Zapier ("QUAND edge ≥ 8% ET ligue ∈ {L1, PL, UCL} → NOTIFIER Telegram + Push").

### Structure

1. **Canaux** (3 cards) :
   - Telegram (connexion via bot + deep link `@probalab_bot?start=TOKEN`)
   - Email (vérification automatique)
   - Push web navigateur (Service Worker + VAPID keys, déjà présent backend via `pywebpush`)
2. **Règles d'alerte** (liste + builder) :
   - Règles pré-créées au signup : `Safe du jour · kick-off 1h`, `Value bets haut edge` (edge ≥ 8%)
   - Chaque règle : toggle on/off + menu `⋯` (edit/supprimer)
   - Affichage compact : chips QUAND / ET / NOTIFIER en ligne
   - Bouton `+ Ajouter une règle sur mesure` → modal builder
3. **Rule builder modal** :
   - Conditions composables : `edge ≥ X%`, `ligue ∈ {...}`, `sport = foot|nhl`, `confiance = élevée`, `kick-off dans < X min`, `bankroll ↓ X% sur Yj`
   - Logique : AND/OR entre conditions (limité à 3 conditions max en V1)
   - Canaux de sortie : multi-select Telegram/Email/Push
   - Action secondaire optionnelle : ex `+ pause paris suggérée` pour drawdown critique

### Endpoints
- `GET /api/user/notifications/channels` — statut canaux
- `POST /api/user/notifications/channels/telegram/connect` — lier Telegram
- `POST /api/user/notifications/rules` — créer règle
- `PUT /api/user/notifications/rules/:id` — modifier règle
- `DELETE /api/user/notifications/rules/:id` — supprimer règle

---

## 13. Responsive & accessibilité

### Mobile-first strict

Design de base à 375px (iPhone SE), ajustements progressifs :
- `sm` (640px+) : gouttières un peu plus larges
- `md` (768px+) : tablet layout, certaines listes 2 colonnes
- `lg` (1024px+) : desktop base avec sidebars et sticky
- `xl` (1280px+) : max-width 1200px centré

### Accessibilité

- Contraste WCAG AA minimum partout (vérifier palette avec `axe-core`)
- Jamais de texte sous 12px
- Infos critiques (edge, odds, probas) ≥ 14px
- Focus visible sur tous les éléments interactifs (`outline: 2px solid var(--primary)`)
- ARIA labels sur tous les boutons icônes et toggles
- Lecteurs d'écran : les barres de probas ont un label complet (`aria-label="PSG 58%, Nul 24%, Lens 18%"`)
- Navigation clavier complète (tab order cohérent)

### Performance

- Lazy load des routes via `React.lazy` (déjà en place)
- Lazy load des graphiques recharts (chunk séparé)
- Images des logos équipes en `<picture>` avec webp + fallback
- Mise en cache React Query : 5 min pour predictions, 30 min pour stats historiques, 15 min pour track record live
- Target Lighthouse Performance > 85, Accessibility > 95

---

## 14. Changements backend induits

La plupart des endpoints existent déjà. Changements nécessaires :

### Nouveaux endpoints
- `GET /api/safe-pick?date=today` — pronostic Safe curated du jour (sélection automatique matchs cote 1.8–2.2 avec confiance élevée)
- `GET /api/public/track-record/live` — KPIs publics CLV/ROI/Brier, cache 5 min
- `GET /api/matches` — consolidation football + NHL avec filtres
- `GET /api/odds/:fixtureId/comparison` — comparateur par book
- `GET /api/analysis/:fixtureId` — analyse Gemini structurée
- `GET /api/user/bankroll/roi-by-market` — breakdown
- `POST /api/user/notifications/rules` (+ PUT/DELETE) — CRUD règles
- Endpoints Telegram connect flow

### Endpoints modifiés
- `/api/best-bets` → ajouter filtre `min_bookmakers`, retourner `meilleure_cote_par_book`
- `/api/predictions/:fixtureId` → inclure `tous_marches` structuré (actuellement partiellement dans stats_json)

### Backend non impacté
- Ingestion odds, pipeline ML, CLV engine — tout est en place (H2-SS1 déployé).

---

## 15. Migration & coexistence

- **Feature flag** : `FRONTEND_V2_ENABLED` côté frontend (env var Vite) pour basculer graduellement.
- **Route de preview** : `/v2/*` pour tester en prod avant cutover.
- **Données user préservées** : bankroll actuel migré depuis la Watchlist existante (si présente) + paris best-bets suivis.
- **Cutover** : activation du flag en une seule fois après tests complets, redirects 301 des anciennes routes vers nouvelles (`/paris-du-soir` → `/matchs?filter=value`, `/football` → `/matchs?sport=foot`, etc.).

---

## 16. Tests & critères d'acceptation

### Fonctionnels
- Un visiteur non-connecté peut voir la landing `/`, cliquer "Essai gratuit 30 jours" et s'inscrire en < 60s sans carte bancaire.
- Un user free voit immédiatement le Safe du jour à l'arrivée sur `/` connecté.
- Un user premium peut créer une règle d'alerte custom et la recevoir sur Telegram en < 5 min.
- Le comparateur de cotes sur la fiche match montre toujours ≥ 3 bookmakers quand dispo.
- Le track record live `/premium` se rafraîchit bien toutes les 15 min (cache côté client).

### Non-fonctionnels
- Lighthouse Performance ≥ 85 sur `/` et `/matchs` (mobile & desktop).
- Lighthouse Accessibility ≥ 95 sur toutes les pages refaites.
- Bundle JS initial < 250 Ko gzippé (hors charts lazy-loadés).
- First Contentful Paint < 1.5s sur 4G simulée.
- Zero console error / warning en production.

### Qualité code
- Tous les composants typés TypeScript strict.
- Tests unitaires sur composants système (`StatTile`, `ProbBar`, `ValueBadge`, etc.) via Vitest.
- Test E2E Playwright sur les 3 parcours principaux (inscription → trial, visiteur → voir match → CTA premium, premium → créer règle alerte).

---

## 17. Hors scope V1 (backlog)

- Page Admin refonte (SS2, après observation CLV 7+ jours)
- Page Performance refonte (SS2)
- Mode sombre/clair toggle UI (structure en place, UI toggle V1.1)
- Support multi-langue (FR uniquement V1)
- PWA installable (phase 2)
- Notifications push mobiles natives (iOS/Android, via Capacitor — V2 majeure)
- Comparateur de pronostiqueurs externes (concurrence) — V2

---

## 18. Risques & mitigations

| Risque | Impact | Mitigation |
|---|---|---|
| CLV sort négatif sur les 7 premiers jours | Argument "preuve par la transparence" contre-productif | Garder garantie transparence ("mois offert"), afficher window 30j pour lisser, communiquer "early days" sur les 30 premiers jours en note bas de page |
| Endpoint `safe-pick` retourne rien (pas de match cote 1.8-2.2 confiance élevée ce jour) | Page Accueil connectée sans Safe | Fallback : afficher "Pas de pronostic Safe aujourd'hui — privilégiez l'analyse des matchs du soir" + liste curated 3 matchs à forte confiance |
| Perf mobile dégradée par charts recharts | Lighthouse < 85 | Lazy load charts, remplacer par SVG custom léger si besoin sur Accueil (conserver recharts pour Bankroll uniquement) |
| Rules builder trop complexe pour user débutant | Pas d'usage, feature morte | Pré-création de 2 règles par défaut au signup, UI "templates" avant builder avancé, wording simple (`QUAND / ALORS`) |
| Gating post-trial trop agressif → churn | Conversion trial → premium faible | Mode "révélation progressive" (pas full-gate) : 1 value bet visible, 1er paragraphe IA visible — démontre la qualité avant de bloquer |

---

## 19. Prochaines étapes

1. **User review de ce spec** (gate actuel)
2. **Plan d'implémentation détaillé** (via skill `writing-plans`) découpant en tâches séquentielles avec TDD
3. **Implémentation par sous-agents** selon le plan validé
4. **Review progressive** après chaque page majeure (Home → Matches → MatchDetail → Premium → Bankroll → Account)
