# Sport Intelligence Dashboard — Design Spec

**Date** : 2026-04-27
**Statut** : Validé oralement, prêt pour plan d'implémentation
**Périmètre** : Repositionnement UX/UI du frontend V2 autour des analyses et probabilités sportives

---

## 1. Positionnement

ProbaLab n'est pas une app de trading, pas un média sportif à rédiger, pas un simple site de tips. Le produit devient :

> Une app premium d'analyses et probabilités sportives pour aider les parieurs à mieux décider.

Le pari reste le cas d'usage final, mais l'expérience doit vendre la qualité de l'analyse : probabilités précises, lecture du match, signaux de confiance, scénarios probables, pronos recommandés.

### Promesse principale

- Comprendre les matchs avant de parier.
- Voir les probabilités clés sans bruit.
- Recevoir des pronos comme sortie du modèle, pas comme unique promesse.
- Lire des explications courtes générées automatiquement par IA quand la donnée le permet.

### Ce qu'on arrête de mettre au centre

- `trading desk`, `value desk`, `market pulse`, `ticket contrôlé`.
- `CLV`, `Pinnacle`, `quant fund`, `Kelly`, `Brier`, `edge` comme vocabulaire principal.
- L'imaginaire finance/trader.
- Les value bets comme axe d'identité de toute l'app.

Ces concepts peuvent rester en détail avancé ou en aide contextuelle, mais ne doivent plus définir le premier niveau de lecture. Même un parieur aguerri doit comprendre l'écran sans connaître le vocabulaire trading/statistique.

---

## 2. Utilisateurs et conversion

### Cible

- **Parieur occasionnel sérieux** : veut savoir quoi regarder, quelles probabilités croire, quels pronos suivre.
- **Parieur intermédiaire** : veut comparer les marchés et comprendre pourquoi un match est intéressant.
- **Utilisateur premium potentiel** : paye si l'app donne une impression de précision, de sérieux et de gain de temps.

### Objectif business

Créer une UX assez qualitative pour justifier un abonnement :

- perception premium dès l'accueil ;
- accès rapide aux meilleurs matchs et pronos ;
- explications assez claires pour créer la confiance ;
- gating progressif qui montre la valeur sans frustrer ;
- pas de dépendance à de la rédaction manuelle.

---

## 3. Direction visuelle validée

Nom de direction : **Sport Intelligence Dashboard**.

Ton visuel :

- dark premium, mais plus sport/data/IA que finance ;
- bleu/cyan comme couleur de confiance et précision ;
- vert réservé aux signaux positifs, pas à toute l'identité ;
- ambre réservé au premium ou aux opportunités ;
- cartes aérées, lisibles, moins denses que le trading cockpit ;
- chiffres très lisibles, mais accompagnés de texte humain.

### Palette cible

- `--bg`: nuit bleutée `#07111f`
- `--surface`: ardoise profonde `#0f172a`
- `--surface-2`: bleu nuit `#111827`
- `--border`: slate translucide
- `--text`: blanc froid `#f8fafc`
- `--text-muted`: `#94a3b8`
- `--primary`: bleu confiance `#60a5fa`
- `--accent`: cyan IA/data `#22d3ee`
- `--positive`: vert `#34d399`
- `--premium`: ambre `#fbbf24`
- `--danger`: rose/rouge `#fb7185`

---

## 4. Hiérarchie produit

### Accueil connecté

Objectif : scanner la journée et comprendre où l'analyse ProbaLab apporte de la valeur.

Ordre recommandé :

1. **Hero dashboard**
   Titre : `Analyses et probabilités sportives`
   Sous-texte : `Les matchs du jour, les probabilités clés et les signaux du modèle pour décider plus vite.`

2. **Résumé de journée**
   - nombre de matchs analysés ;
   - meilleurs niveaux de confiance ;
   - sports/ligues disponibles ;
   - dernière mise à jour.

3. **Matchs à suivre**
   Liste priorisée par intérêt analytique, pas uniquement par value bet. Chaque ligne affiche :
   - équipes, ligue, heure ;
   - probas 1X2 ;
   - niveau de confiance ;
   - tags `Prono`, `Match ouvert`, `Favori solide`, `Analyse premium`.

4. **Prono recommandé**
   Une section claire, mais secondaire : Safe du jour / sélection modèle.

5. **Performance / preuve**
   ROI, précision, qualité des probabilités, calibration, mais en langage accessible.

### Page détail match

Objectif : aider à comprendre le match avant le pari.

Ordre recommandé :

1. **Hero match**
   Ligue, heure, équipes, forme, contexte.

2. **Lecture du match**
   Bloc principal avec :
   - probas 1X2 ;
   - scénario probable ;
   - niveau de confiance ;
   - points de vigilance.

3. **Analyse IA courte**
   Générée automatiquement. Format court :
   - `Ce que le modèle voit`
   - `Pourquoi ce match est intéressant`
   - `Risques à surveiller`

4. **Marchés et probabilités**
   1X2, double chance, BTTS, over/under, autres marchés selon disponibilité.

5. **Prono / recommandation**
   Affiché comme conclusion possible, pas comme entrée unique.

6. **Détails avancés premium**
   Cotes bookmakers, signal modèle, mise prudente, suivi bankroll, si utile.

---

## 5. Wording à appliquer

### Remplacer

- `ProbaLab trading desk` → `Centre d'analyse ProbaLab`
- `Cockpit du jour` → `Analyses du jour`
- `Market pulse` → `Résumé de journée`
- `Value desk` → `Opportunités du jour` ou `Pronos recommandés`
- `Decision cockpit` → `Lecture du match`
- `Ticket contrôlé` → `Prono recommandé`
- `Risque bankroll` → `Niveau de risque`
- `Fair odds` → `Cote juste modèle`
- `CLV vs Pinnacle` → `Signal marché`
- `Brier` → `Qualité des probabilités`
- `Kelly` → `Mise prudente` ou `mise suggérée`
- `edge` → `Signal modèle`
- `quant fund` → `méthode claire et vérifiable`

### Vocabulaire principal

- analyses sportives ;
- probabilités ;
- confiance modèle ;
- scénario probable ;
- points de vigilance ;
- pronos recommandés ;
- marchés clés ;
- explication IA ;
- performance du modèle.

---

## 6. IA et contenu éditorial

Pas de modèle éditorial manuel. Toute analyse narrative doit être générée automatiquement à partir de données structurées.

Règles :

- pas d'articles longs ;
- pas de rédaction manuelle récurrente ;
- analyses courtes et actionnables ;
- afficher la date de génération ;
- fallback silencieux si l'IA n'est pas disponible : les probabilités et stats restent l'expérience principale.

Format cible :

- 2 à 4 paragraphes courts ;
- puces si possible ;
- langage clair ;
- toujours lié aux données disponibles.

---

## 7. Gating premium

Le gating doit vendre la qualité sans masquer tout le produit.

Visible gratuitement :

- matchs du jour ;
- probas 1X2 de base ;
- un prono recommandé ;
- aperçu d'analyse courte.

Premium :

- analyses IA complètes ;
- marchés avancés ;
- explications détaillées ;
- comparateur de cotes ;
- opportunités avancées/value ;
- historique performance plus complet ;
- alertes et suivi bankroll.

---

## 8. Critères de réussite UX/UI

La nouvelle interface doit :

- être compréhensible en moins de 10 secondes sur l'accueil ;
- donner une impression de précision et de sérieux ;
- éviter le jargon betting avancé au premier niveau ;
- rendre les pronos désirables sans transformer l'app en site de tips ;
- faire comprendre pourquoi l'abonnement débloque une meilleure analyse ;
- fonctionner aussi bien en mobile qu'en desktop ;
- conserver les tests existants et ajouter des tests de wording/hiérarchie sur les écrans refondus.

---

## 9. Première tranche d'implémentation

La première passe doit rester concentrée :

1. Rewording et redesign de l'accueil connecté.
2. Rewording et redesign de la page détail match.
3. Renommage ou remplacement de `ValueBetsTeaser` en section plus généraliste.
4. Suppression du vocabulaire trading/value au premier niveau.
5. Mise à jour des tests frontend associés.
6. Ajout d'une leçon projet après implémentation.

Hors scope immédiat :

- refonte complète landing visiteur ;
- nouvelles routes ;
- nouvelle génération IA backend ;
- refonte pricing ;
- refonte admin/performance.
