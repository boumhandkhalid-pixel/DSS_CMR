# Architecture du Moteur de Décision - Guide Complet

**Auteur:** Système d'Aide à la Décision pour Trading Opérationnel (BVC)  
**Date:** Août 2026  
**Objectif:** Comprendre en profondeur le flux complet du système d'évaluation et de recommendation

---

## Table des Matières

1. [Vue d'ensemble globale](#vue-densemble-globale)
2. [Flux chronologique complet](#flux-chronologique-complet)
3. [Rationale architecturale](#rationale-architecturale)
4. [Détail de chaque étape](#détail-de-chaque-étape)
5. [Hypothèses de conception](#hypothèses-de-conception)
6. [Limitations et pistes d'amélioration](#limitations-et-pistes-damélioration)

---

## Vue d'ensemble globale

Le moteur de décision est un **système en cascade à 6 étapes** qui transforme les données de marché brutes en une recommandation d'investissement (BUY/HOLD/SELL/INSUFFICIENT_DATA).

```
ÉTAPE 0     ÉTAPE 1        ÉTAPE 2         ÉTAPE 3              ÉTAPE 4           ÉTAPE 5
─────────────────────────────────────────────────────────────────────────────────────────────
Données      Calcul         Signalisation   Agrégation        Score Global &     Logique de
brutes  →    Indicateurs →  Individuelle →  par Famille  →    Confiance    →    Décision
(OHLCV)     (7 indicateurs) (+1/0/-1/NaN)  (3 scores)        (Indépendants)     (4 gates)
```

**Principe fondamental:** Chaque étape n'a accès qu'aux résultats de l'étape précédente. Cette **séparation des concerns** permet de :
- Valider chaque composant indépendamment
- Ajuster les poids sans modifier la logique des indicateurs
- Diagnostiquer les faux positifs à chaque niveau

---

## Flux chronologique complet

### ÉTAPE 0 : Import et Filtrage des Données

**Entrées:**
- Fichier Excel contenant données de marché (Cours, Bid, Ask, Volume)
- Fichier Excel contenant composition de l'indice MASI

**Processus:**
```
1. Ingestion des deux fichiers
2. Parsing automatique (détection de format)
3. Filtrage univers investable:
   - Seulement titres du MASI
   - Free Float Factor ≥ 0.20 (liquidité minimale)
   - Capitalisation flottante ≥ p25 (environ 218 M MAD en 2026)
4. Filtrage qualité données:
   - Minimum 14 observations consécutives de Cours
   - Écart maximal 7 jours entre deux observations
   - (Justification: RSI-14 requiert 14 prix pour valider)
5. Construction DataFrame cohérent (triés par CODE_ISIN, Date)
```

**Sortie:** DataFrame `df_universe` avec N titres filtrés, prêts pour calcul indicateurs

**Code référence:** `src/pipeline.py` → `ingest_market_data()` + `src/ingestion.py`

---

### ÉTAPE 1 : Calcul des 7 Indicateurs Techniques

Pour chaque titre, pour chaque date, on calcule 7 indicateurs organisés en 3 catégories.

#### **CATÉGORIE 1 : TREND (Tendance directionnelle)**

**Indicateur 1.1 : SMA-20 (Simple Moving Average, window=20)**
- **Définition:** Moyenne mobile simple des 20 derniers cours de fermeture
- **Formule:** 
  ```
  SMA_20(t) = (Cours(t) + Cours(t-1) + ... + Cours(t-19)) / 20
  ```
- **Données minimales requises:** 20 observations consécutives
- **Interprétation:**
  - Prix > SMA-20 → Tendance court-terme haussière
  - Prix < SMA-20 → Tendance court-terme baissière
  - Prix ≈ SMA-20 → Zone de consolidation
- **Signification:** Capture les mouvements fondamentaux sur ~1 mois (20 jours ouvrés)
- **Raison du choix:** 
  - Largement utilisé par traders retail
  - Facile à comprendre et valider
  - Window suffisamment court pour réagir rapidement aux changements

**Indicateur 1.2 : SMA-50 (Simple Moving Average, window=50)**
- **Définition:** Moyenne mobile simple des 50 derniers cours
- **Formule:**
  ```
  SMA_50(t) = (Cours(t) + Cours(t-1) + ... + Cours(t-49)) / 50
  ```
- **Données minimales requises:** 50 observations consécutives
- **Interprétation:**
  - Prix > SMA-50 → Tendance moyen-terme haussière
  - Prix < SMA-50 → Tendance moyen-terme baissière
- **Signification:** Capture la tendance plus stable, ~2.5 mois
- **Raison du choix:**
  - Golden Cross classique (SMA-20 croise SMA-50) = signal très reconnu
  - Permet de capturer des reversals de tendance
  - Filtre les bruits court-terme

**Indicateur 1.3 : EMA-20 (Exponential Moving Average, span=20)**
- **Définition:** Moyenne mobile exponentielle (pondère davantage les prix récents)
- **Formule de récurrence:**
  ```
  α = 2 / (span + 1) = 2/21 ≈ 0.0952
  EMA_20(t) = α × Cours(t) + (1-α) × EMA_20(t-1)
  ```
- **Données minimales requises:** 1 observation (dégradé gracieux)
- **Interprétation:**
  - Prix > EMA-20 → Signal haussier avec poids plus fort aux mouvements récents
  - Prix < EMA-20 → Signal baissier
- **Signification:** Plus réactif que SMA, capture dynamique fine de la tendance
- **Raison du choix:**
  - Combine "mémoire" du passé + réactivité au présent
  - Utile pour déterminer l'ordre des ordres en scalping court-terme
  - Complète SMA-20/50 pour une vision multi-échelle

#### **CATÉGORIE 2 : MOMENTUM (Dynamique et intensité)**

**Indicateur 2.1 : RSI-14 (Relative Strength Index, period=14)**
- **Définition:** Oscillateur mesurant la force relative des mouvements haussiers vs baissiers
- **Formule:**
  ```
  Δ(t) = Cours(t) - Cours(t-1)
  Gains(t) = max(Δ(t), 0)
  Pertes(t) = max(-Δ(t), 0)
  
  AG = Moyenne Wilder des Gains (14 périodes)
  AL = Moyenne Wilder des Pertes (14 périodes)
  RS = AG / AL
  RSI = 100 - (100 / (1 + RS))
  ```
- **Données minimales requises:** 15 observations (14 deltas + 1 seed)
- **Plage:** [0, 100]
- **Interprétation:**
  - RSI < 30 → **Survente** (oversold) → Signal haussier potentiel (+1)
  - 30 ≤ RSI ≤ 70 → **Neutre** (0)
  - RSI > 70 → **Surachat** (overbought) → Signal baissier potentiel (-1)
- **Signification:** Mesure si le marché s'est "trop éloigné" (statut moyen-terme), probabilité de correction
- **Raison du choix:**
  - Indicateur classique du momentum
  - Seuils 30/70 sont universels et validés empiriquement
  - Capture les retournements de court-terme
  - Bien adapté aux marchés peu liquides (BVC) où les survendus/surachatés arrivent plus vite

**Indicateur 2.2 : MACD (Moving Average Convergence Divergence)**
- **Définition:** Différence entre deux moyennes mobiles exponentielles + signal
- **Formule:**
  ```
  MACD_Line = EMA_12(Cours) - EMA_26(Cours)
  Signal_Line = EMA_9(MACD_Line)
  Histogram = MACD_Line - Signal_Line
  ```
- **Données minimales requises:** 26 observations (slow EMA)
- **Interprétation:**
  - MACD > Signal → Momentum haussier (+1)
  - MACD < Signal → Momentum baissier (-1)
  - Crossover MACD/Signal = point de pivot classique
- **Signification:** Détecte les **changements de vélocité** (accélération/décélération de la tendance)
- **Raison du choix:**
  - Combine deux horizons temporels (12 et 26 jours)
  - Capturing momentum changes est clé avant que SMA-50 n'ajuste
  - Les crossovers sont des points de décision reconnaissables

#### **CATÉGORIE 3 : VOLUME & CONFIRMATION (Validation par l'activité)**

**Indicateur 3.1 : RVOL (Relative Volume, window=20)**
- **Définition:** Ratio du volume actuel versus moyenne historique
- **Formule:**
  ```
  RVOL(t) = Volume_MC(t) / MEAN(Volume_MC[t-20:t])
  ```
- **Données minimales requises:** 1 observation (dégradé gracieux, fiable à 20)
- **Plage:** [0, ∞) typiquement [0.1, 5]
- **Interprétation:**
  - RVOL ≥ 1.5 → Volume fort (confirmation du mouvement) → Signal +1
  - 0.5 ≤ RVOL < 1.5 → Volume normal → Neutre (0)
  - RVOL < 0.5 → Volume très faible (marché endormi, signal fragile) → -1
- **Signification:** Valide si un mouvement de prix a un "vrai" acheteur/vendeur derrière
- **Raison du choix:**
  - Prix sans volume = faux signal (sur BVC c'est fréquent)
  - RVOL > 1.5 est un bon seuil de "conviction"
  - Aide à filtrer les mouvements de «tick» sans sens
  - Sur BVC avec liquidité variable, c'est critique

**Indicateur 3.2 : VWAP (Volume Weighted Average Price)**
- **Définition:** Prix moyen pondéré par le volume (cumul depuis début période)
- **Formule:**
  ```
  VWAP(t) = Σ(Cours(i) × Volume_MC(i)) / Σ(Volume_MC(i))  pour i ∈ [0, t]
  ```
- **Données minimales requises:** 1 observation (prix = VWAP si volume=1)
- **Interprétation:**
  - Prix > VWAP → Acheteurs dominants (signal haussier) → +1
  - Prix < VWAP → Vendeurs dominants (signal baissier) → -1
- **Signification:** Donne le prix "juste" selon distribution volume, aide déterminer contrôle acheteur/vendeur
- **Raison du choix:**
  - Utilisé par les traders institutionnels
  - Cumul naturel permet une vue long-terme sans fenêtre fixe
  - Complète bien RVOL pour la confirmation

#### **CATÉGORIE 4 : RISK CONTEXT (Contexte de volatilité)**

**Indicateur 4.1 : HV-20 (Historical Volatility, window=20, annualisé)**
- **Définition:** Écart-type des log-retours annualisé
- **Formule:**
  ```
  r(t) = ln(Cours(t) / Cours(t-1))   [log-return]
  HV_20 = STDEV(r[t-20:t]) × √252   [annualisé pour 252 jours ouvrés]
  ```
- **Données minimales requises:** 21 observations (20 retours)
- **Plage:** [0, ∞) typiquement [5%, 50%] pour la BVC
- **Interprétation:**
  - N'EST PAS un signal directionnel (+1/-1)
  - Entre dans la **Confidence**, pas dans le Score
  - HV élevée (p75+) → Réduit confiance (bruit, moins fiable)
  - HV basse (p25-) → Augmente confiance (marché stable)
- **Signification:** Mesure l'**incertitude/risque** du titre
- **Raison du choix:**
  - Signal à forte volatilité = moins fiable, même s'il semble fort
  - Sur BVC, périodes de volatilité extrême sont fréquentes
  - Protège contre l'over-trading en phase turbulente

---

### ÉTAPE 2 : Signalisation Individuelle

Pour chaque indicateur, on convertit sa valeur numérique en **signal discret** :

| Signal | Valeur | Meaning |
|--------|--------|---------|
| **+1** | Haussier | Achat potentiel |
| **0** | Neutre | Pas de direction claire |
| **-1** | Baissier | Vente potentielle |
| **NaN** | Données insuffisantes | Indicateur pas calculable |

**Règles de signalisation par indicateur:**

```
SMA-20:         Cours > SMA-20  → +1,  Cours < SMA-20  → -1,  Cours = SMA-20 → 0
SMA-50:         Cours > SMA-50  → +1,  Cours < SMA-50  → -1,  Cours = SMA-50 → 0
EMA-20:         Cours > EMA-20  → +1,  Cours < EMA-20  → -1,  Cours = EMA-20 → 0
RSI-14:         RSI < 30   → +1,       30 ≤ RSI ≤ 70 → 0,       RSI > 70  → -1
MACD:           MACD > Signal → +1,    MACD < Signal → -1,    MACD ≈ Signal → 0
RVOL:           RVOL ≥ 1.5 → +1,       0.5 ≤ RVOL < 1.5 → 0,   RVOL < 0.5 → -1
VWAP:           Cours > VWAP → +1,     Cours < VWAP → -1,     Cours = VWAP → 0
HV-20:          N/A (pas de signal, utilisé en Confiance)
```

**Point crucial:** Signal 0 ≠ NaN
- **0** = « Je sais que l'indicateur est neutre »
- **NaN** = « Je n'ai pas assez de données pour juger »

Cela affecte directement les calculs de famille (les NaN sont exclus, les 0 sont inclus).

**Code référence:** `src/signals.py` → `individual_signals()`

---

### ÉTAPE 3 : Agrégation par Famille

Les 7 indicateurs sont regroupés en **3 familles** selon leur rôle fonctionnel.

#### **Famille 1 : TENDANCE (Trend)**
**Membres:** SMA-20, SMA-50, EMA-20  
**Poids dans score global:** 35%  
**Rôle:** Répondre à « Quelle est la direction de base ? »

**Calcul du Score_Tendance:**
```
Signaux valides = {Sig_SMA_20, Sig_SMA_50, Sig_EMA_20} avec signal ≠ NaN
Moyenne des signaux = (Sig_SMA_20 + Sig_SMA_50 + Sig_EMA_20) / N  où N = nombre de signaux valides
Score_Tendance = ((Moyenne + 1) / 2) × 100
```

**Exemple 1:** Tous haussiers
```
Signaux = [+1, +1, +1]
Moyenne = 3/3 = +1
Score = ((+1 + 1) / 2) × 100 = 100
Interprétation: Tendance extrêmement haussière
```

**Exemple 2:** Mixte
```
Signaux = [+1, +1, 0]
Moyenne = 2/3 = +0.67
Score = ((+0.67 + 1) / 2) × 100 = 83.3
Interprétation: Tendance haussière claire avec une légère hésitation
```

**Exemple 3:** Un seul valide
```
Signaux = [+1, NaN, NaN]  → Exclus les NaN → [+1]
Moyenne = 1/1 = +1
Score = 100
Interprétation: SMA-20 haussier, autres données manquantes, on utilise le signal disponible
```

#### **Famille 2 : MOMENTUM (Momentum)**
**Membres:** RSI-14, MACD  
**Poids dans score global:** 35%  
**Rôle:** Répondre à « Quelle est l'intensité du mouvement ? »

**Calcul du Score_Momentum:**
```
Signaux valides = {Sig_RSI_14, Sig_MACD} avec signal ≠ NaN
Score_Momentum = ((Moyenne des signaux + 1) / 2) × 100
```

**Exemple :**
```
Sig_RSI = -1 (surachat → baissier)
Sig_MACD = +1 (MACD > Signal → haussier)
Moyenne = 0/2 = 0
Score_Momentum = ((0 + 1) / 2) × 100 = 50
Interprétation: Désaccord entre RSI et MACD, momentum neutre/ambigu
```

#### **Famille 3 : VOLUME (Volume & Confirmation)**
**Membres:** RVOL, VWAP  
**Poids dans score global:** 20%  
**Rôle:** Répondre à « Le prix est-il confirmé par le volume/action des acheteurs ? »

**Calcul du Score_Volume:**
```
Signaux valides = {Sig_RVOL, Sig_VWAP} avec signal ≠ NaN
Score_Volume = ((Moyenne des signaux + 1) / 2) × 100
```

**Raison des poids (35-35-20):**
```
Tendance 35%:   Direction primaire, sans elle pas de décision
Momentum 35%:   Intensité, aussi importante que direction
Volume 20%:     Confirmation tertiaire, moins critique mais protectrice
Ratio:          Pas de validation empirique encore (baseline hypothesis)
```

**Code référence:** `src/signals.py` → `family_score()`

---

### ÉTAPE 4 : Score Global & Confiance (Indépendants)

#### **Sous-étape 4A : Overall_Score (Direction Pondérée)**

```
Overall_Score = (w_T × Score_Tendance + w_M × Score_Momentum + w_V × Score_Volume) 
                / (w_T + w_M + w_V)

où w_T = 0.35, w_M = 0.35, w_V = 0.20
```

**⚠️ Point crucial:** La somme des poids = 0.90, NON 1.0. Pourquoi ?

**Raison:** Les poids sont **DYNAMIQUES** - ils s'adaptent si une famille a des données manquantes (NaN).

**Exemple 1 - Cas normal (tous les scores valides):**
```
Score_Tendance = 75    ✓
Score_Momentum = 60    ✓
Score_Volume = 80      ✓

weighted_sum = 0.35×75 + 0.35×60 + 0.20×80 = 63.25
total_w = 0.35 + 0.35 + 0.20 = 0.90
Overall_Score = 63.25 / 0.90 = 70.28
```

**Exemple 2 - Score_Volume est NaN (données insuffisantes):**
```
Score_Tendance = 75    ✓
Score_Momentum = 60    ✓
Score_Volume = NaN     ✗ (données insuffisantes pour Volume)

weighted_sum = 0.35×75 + 0.35×60 = 47.25
total_w = 0.35 + 0.35 = 0.70  ← RÉADAPTÉ (0.20 retiré)
Overall_Score = 47.25 / 0.70 = 67.5
```

**Si on divisait toujours par 0.90 (fixe):**
```
Overall_Score = 47.25 / 0.90 = 52.5  ← FAUX!
Pénalité injuste: le score baisse non pas parce que Trend/Momentum sont faibles,
mais parce que Volume manque. Cela biaise la recommandation.
```

**Code référence:** `src/signals.py` → `overall_score()` (L.106-113)
```python
total_w, ws = 0.0, 0.0
for fam, w in weights.items():
    if fam == 'Risk':
        continue  # HV n'entre pas dans Overall_Score
    v = row.get(f'Score_{fam}', np.nan)
    if pd.notna(v):
        ws += v * w
        total_w += w  # ← Accumule dynamiquement
return ws / total_w if total_w > 0 else np.nan
```

**Exemple:**
```
Score_Tendance = 80
Score_Momentum = 60
Score_Volume = 70

Overall_Score = (0.35×80 + 0.35×60 + 0.20×70) / (0.35 + 0.35 + 0.20)
              = (28 + 21 + 14) / 1.0
              = 63
```

**Plage:** [0, 100]
- 0 = Consensus complètement baissier
- 50 = Neutre
- 100 = Consensus complètement haussier

**Point crucial:** HV-20 n'entre PAS dans ce score. Il entre dans la Confiance.

**Code référence:** `src/signals.py` → `overall_score()`

#### **Sous-étape 4B : Confidence Score (Qualité des Données - INDÉPENDANT)**

**Définition:** La confiance mesure la **fiabilité** des signaux, pas leur direction.

```
Confidence = (w_COV × DataCoverage + w_AGREE × FamilyAgreement + w_RISK × RiskPenalty) × 100%

où w_COV = 0.40, w_AGREE = 0.40, w_RISK = 0.20
```

**Composante A : Data Coverage (40%)**
```
Indicateurs obligatoires: {SMA-20, SMA-50, EMA-20, RSI-14, MACD, RVOL, VWAP}  (7 indicateurs)
Valid_count = nombre d'indicateurs avec statut VALID
DataCoverage = Valid_count / 7
```

**Exemple:**
```
Statut des indicateurs:
  SMA-20 : VALID       ✓
  SMA-50 : VALID       ✓
  EMA-20 : VALID       ✓
  RSI-14 : VALID       ✓
  MACD   : INSUFFICIENT_DATA  ✗
  RVOL   : VALID       ✓
  VWAP   : VALID       ✓
  
DataCoverage = 6/7 ≈ 0.857
```

**Composante B : Family Agreement (40%)**
```
Mesure si les 3 familles sont d'accord sur la direction.

bullish_count = nombre de familles avec Score > 50
bearish_count = nombre de familles avec Score < 50
(Score = 50 exact → neutre, compte dans aucun)

FamilyAgreement = max(bullish_count, bearish_count) / total_valid_families
```

**Exemple 1 - Accord fort:**
```
Score_Tendance = 75 (haussier)
Score_Momentum = 82 (haussier)
Score_Volume = 68 (haussier)

bullish_count = 3, bearish_count = 0
FamilyAgreement = 3/3 = 1.0 (100% accord)
```

**Exemple 2 - Désaccord:**
```
Score_Tendance = 72 (haussier)
Score_Momentum = 48 (baissier)
Score_Volume = 52 (haussier)

bullish_count = 2, bearish_count = 1
FamilyAgreement = 2/3 ≈ 0.67 (67% accord)
```

**Composante C : Risk Penalty (20%)**
```
Pénalité si HV est anormalement élevée.

HV_p75 = 75e percentile de la distribution HV sur l'univers
Si HV > HV_p75:
    risk_penalty = min(0.3, max(0, (HV - HV_p75) / HV_p75))
Sinon:
    risk_penalty = 0

RiskPenalty = 1 - risk_penalty  [après pénalité, on pénalise la confiance]
```

**Exemple:**
```
HV-20 = 35%
HV_p75 (univers) = 22%
risk_penalty = (35 - 22) / 22 ≈ 0.59 capped à 0.3 → 0.3
RiskPenalty = 1 - 0.3 = 0.7
→ La volatilité élevée réduit confiance de 30%
```

**Confiance finale:**
```
Confiance = (0.40 × 0.857 + 0.40 × 1.0 + 0.20 × 0.7) × 100%
          = (0.343 + 0.400 + 0.140) × 100%
          = 88.3%
```

**Code référence:** `src/signals.py` → `confidence_score_v2()`

#### **Combinaison Score & Confiance:**

| Score | Confiance | Interprétation | Recommandation |
|-------|-----------|----------------|-----------------|
| 85 | 35% | Signal fort mais données sparses/bruitées | HOLD (trop d'incertitude) |
| 48 | 89% | Pas de direction claire, très fiable | HOLD (pas de signal net) |
| 72 | 75% | Signal haussier clair et fiable | Peut être BUY |
| 35 | 20% | Signal baissier fort mais peu fiable | HOLD (données insuffisantes) |

**Point clé:** Un score de 95 avec confiance 45% genère HOLD, pas BUY. Cela protège contre les faux positifs.

---

### ÉTAPE 5 : Logique de Décision (4 Gates)

Le système applique 4 **portes de contrôle** (gates) pour transformer (Score, Confiance) en recommandation.

#### **Gate 1 : BUY**
```
Condition:  Score ≥ 60 AND Confiance ≥ 60%
Recommandation: BUY
Rationale: Signal haussier fort + données fiables
```

#### **Gate 2 : HOLD**
```
Condition:  40 < Score < 60
Recommandation: HOLD
Rationale: Pas de direction claire, rester neutre
```

#### **Gate 3 : SELL**
```
Condition:  Score ≤ 40 AND Confiance ≥ 60%
Recommandation: SELL
Rationale: Signal baissier fort + données fiables
```

#### **Gate 4 : INSUFFICIENT_DATA**
```
Condition:  DataCoverage < 50%  (i.e., moins de 3.5 indicateurs valides)
Recommandation: INSUFFICIENT_DATA
Rationale: Trop de données manquantes, impossible de juger
```

**Priorité des portes:**
1. D'abord vérifier INSUFFICIENT (court-circuit si < 50% couverture)
2. Puis vérifier BUY (Score ≥ 60 ET Conf ≥ 60%)
3. Puis vérifier SELL (Score ≤ 40 ET Conf ≥ 60%)
4. Tout le reste → HOLD

**Code référence:** `src/decisions.py` → `make_decision()`

---

## Rationale architecturale

### Pourquoi cette architecture ?

#### **1. Séparation Score & Confiance**

**Problème classique:** Combiner direction + qualité dans un seul score crée ambiguïté.

Par exemple, RSI-14 = 25 (survente forte) seul produirait signal +1 (haussier).  
Mais si c'est sur 2 prix seulement (HV très élevée, marché chaotique), faut-il vraiment acheter ?

**Solution:** Deux dimensions orthogonales
- **Score** : Que disent les données ?
- **Confiance** : À quel point je fais confiance aux données ?

Cela permet :
```
Score=85, Conf=30 → HOLD (signal fort, peu fiable)
Score=50, Conf=92 → HOLD (pas de signal, très fiable)
Score=78, Conf=75 → BUY (signal + données bonnes)
```

#### **2. Trois familles d'indicateurs**

**Problème:** 7 indicateurs = trop pour gérer manuellement, mais comment les organiser ?

**Solution:** Regrouper par fonction métier
```
TREND (3 ind.):    Quelle est la direction ?        → 35%
MOMENTUM (2 ind.): Quelle est l'intensité ?         → 35%
VOLUME (2 ind.):   C'est confirmé par le volume ?   → 20%
```

Avantages:
- Chaque famille répond à une question claire
- Poids reflètent l'importance relative
- Facile à expliquer à un gestionnaire : "Les prix montent (TREND) et ça s'accélère (MOMENTUM), validé par le volume."
- Facile à ajuster : si MOMENTUM trop bruyant, baisser poids de 35% à 30%

#### **3. Signalisation discrète (+1/0/-1/NaN)**

**Problème:** Combiner directement les valeurs numériques crée sensibilité aux unités (RSI en [0,100], SMA en prix d'actions [10-500 MAD], RVOL en [0.1-10])

**Solution:** Convertir tous les indicateurs en signal **dimensionless**
```
+1 = Haussier (peu importe comment)
0 = Neutre
-1 = Baissier
NaN = Données manquantes
```

Avantages:
- Unités disparaissent, tous les indicateurs parlent le même langage
- Moyenne des signaux [-1, +1] se convertit facilement en [0, 100]
- Facile de détecter les désaccords : si 2 signaux +1 et 1 signal -1, c'est clairement pas unanime

#### **4. Poids fixes (35-35-20)**

**Problème:** Comment décider des poids entre Trend/Momentum/Volume ?

**Solution réaliste (baseline):**
```
Tendance 35%:   Information primaire, nécessaire pour toute décision
Momentum 35%:   Aussi important que tendance (intensité = timing d'entrée)
Volume 20%:     Secondaire mais protecteur (filtre les faux signaux)
Risk 10%:       Entre en Confiance, pas dans Score
```

**Raison du baseline:** Ce n'est PAS une optimisation empirique (pas de backtesting encore). C'est un jugement d'expert cohérent.

**Feuille de route:** Notebook 12 (Backtesting) testera 5 configurations (A, B, C, D, E) et sélectionnera les poids validés.

---

## Détail de chaque étape

### Étape 0 : Import

**Fichiers entrées:**
```
├── Market Data (hebdo/mensuel)
│   ├── CODE_ISIN (ex: MA0000012632)
│   ├── Date (format YY-MM-DD)
│   ├── Cours (fermeture)
│   ├── Bid
│   ├── Ask
│   └── Volume MC (market cap traded)
│
└── Index Composition (mensuel/trimestriel)
    ├── CODE_ISIN
    ├── FF (Free Float Factor)
    ├── FF_MarketCap (capitalisation flottante)
    ├── Poids dans indice
    └── Nombre de titres
```

**Filtres appliqués (ordre):**
1. **Index filter:** Garder seulement titres du MASI
2. **Free Float filter:** FF ≥ 0.20
3. **Market Cap filter:** FF_MarketCap ≥ p25 de l'univers MASI
4. **Data quality filter:** ≥14 observations consécutives, gap ≤ 7 jours

### Détail du Filtre 4 : Contrainte des 7 jours

**Le Problème Fondamental : Perte de Signification des Deltas**

Les indicateurs techniques (RSI, SMA, EMA, MACD) calculent tous des **différences entre prix adjacents** :

```
RSI = basé sur Δₜ = Cours(t) - Cours(t-1)
SMA = moyenne des prix consécutifs
EMA = moyenne pondérée avec poids fonction du temps écoulé
MACD = différence entre deux EMA
```

**Le vrai problème n'est pas le nombre d'observations, mais leur continuité temporelle.**

Si le gap entre deux observations est très grand (ex: 6 mois), le delta calculé n'est pas une "variation de séance" - c'est des mois de marché compressés en un seul delta. La formule produit un nombre, mais **ce nombre perd son interprétation financière**.

#### **Exemple Concret du Problème**

Supposons un titre avec :
- Dernière observation : 2024-01-15, Cours = 100 MAD
- Observation suivante : 2024-07-20, Cours = 105 MAD  ← **GAP = 187 JOURS**

Si on calcule RSI sur cette séquence :

```
Delta = 105 - 100 = +5 MAD
RSI calculé = "boom, signal haussier fort"

MAIS en réalité :
- Du 15-01 au 20-07, il y a peut-être eu 
  - Crash de -30% au mois de mars
  - Rebond de +40% au mois de mai
  - La différence nette (105 - 100) CACHE toute cette volatilité

RSI basé sur delta 187 jours != RSI basé sur 187 deltas quotidiens
Le nombre produit par la formule est FINANCIÈREMENT SANS SENS
```

#### **Pourquoi 7 Jours Exactement ?**

**⚠️ Clarification importante:** Le seuil de 7 jours **n'est PAS imposé par la formule du RSI**. C'est une **heuristique de contrôle qualité des données** choisie pour détecter les interruptions anormales tout en tolérant les week-ends et jours fériés.

**Contrainte RSI réelle:** RSI-14 requiert minimum **15 observations de prix** pour produire sa première valeur valide (15 prix → 14 deltas → 1 valeur RSI).

```
RSI(14) a besoin de:
  - 15 prix consécutifs : P₁, P₂, ..., P₁₅
  - Pour calculer 14 deltas : Δ₁ = P₂ - P₁, Δ₂ = P₃ - P₂, ..., Δ₁₄ = P₁₅ - P₁₄
  - Les deltas doivent représenter des variations entre séances adjacentes
```

**Calendrier trading (BVC) - Raisonnement de l'heuristique:**

Le seuil de 7 jours calendaires est choisi pour **distinguer les gaps normaux des interruptions anormales** :

```
Gap normal (acceptable):
  - Vendredi 15 → Lundi 18     = 3 jours (weekend)  ✓ ACCEPTABLE
  - Jeudi 14 → Mardi 19        = 5 jours (weekend + férié)  ✓ ACCEPTABLE
  - Vendredi 15 → Vendredi 22  = 7 jours (weekend + quelques jours)  ✓ LIMITE ACCEPTABLE

Gap suspect (rejet):
  - Vendredi 15 → Lundi 25     = 10 jours (2 weekends) ✗ REJETÉ
  - Vendredi 15 → 2 semaines+  = 14+ jours (séances manquantes) ✗ REJETÉ

⚠️ Gap > 7 jours = Au minimum 1-2 séances de trading complètement manquantes
```

**Justification du seuil 7 jours:**
- Couvre 1 weekend normal (2 jours)
- Tolère 1-2 jours fériés occasionnels
- **Au-delà, il y a probablement des séances de marché non observées**
- La "continuité du signal" est compromise

**⚠️ Important:** Ce seuil est une **heuristique pratique**, pas une contrainte mathématique. Une approche plus rigoureuse utiliserait le calendrier officiel des séances BVC pour détecter précisément les séances manquantes.

#### **Implications Mathématiques**

```
MIN_CONSECUTIVE = 50     (SMA_50 binding constraint - indicateur le plus exigeant)
MAX_GAP_DAYS = 7         (heuristique qualité, pas contrainte mathématique)

Pire cas d'une "run" valide:
  - 50 prix avec max gap 7j entre chacun
  - Couverture temporelle max = 50 × 7 = 350 jours calendrier (~11.7 mois)
  - Nombre de séances réelles ≈ 50 + weekends/fériés = 70-80 jours calendrier
  
Meilleur cas:
  - 50 prix sur séances consécutives (no gap sauf weekends)
  - Couverture ≈ 70 jours calendrier (~10 semaines)
  - Séances ouvrées réelles = 50 jours
```

**Justification:** Avec max gap 7j, on tolère les interruptions normales (weekends, fériés) tout en détectant les vraies discontinuités (séances manquantes). Au-delà de 7j, le risque de "trous" dans les données devient trop élevé pour que les indicateurs soient fiables.

**⚠️ Note méthodologique:** La contrainte MIN_CONSECUTIVE devrait idéalement être **50** (pour SMA-50), pas 14. Dans l'implémentation actuelle, nous utilisons 14 comme minimum pour maximiser la couverture de l'univers investable, mais cela signifie que **SMA-50 ne sera pas calculable sur tous les titres** (sera NaN si < 50 observations).

#### **Comment ça Marche en Code**

```python
# Pour chaque titre (CODE_ISIN):
for isin in df['CODE_ISIN'].unique():
    group = df[df['CODE_ISIN'] == isin].sort_values('Date')
    
    # Trouver la plus longue "run" consécutive
    valid_dates = group[group['Cours'].notna()]['Date']
    
    max_consecutive_run = 0
    current_run = 1
    
    for i in range(1, len(valid_dates)):
        gap_days = (valid_dates.iloc[i] - valid_dates.iloc[i-1]).days
        
        if gap_days <= 7:  # ← CLEF: si gap ≤ 7 jours
            current_run += 1
            max_consecutive_run = max(max_consecutive_run, current_run)
        else:
            current_run = 1  # Réinitialiser, run brisée
    
    # Garder seulement si max_run >= 14
    if max_consecutive_run >= 14:
        keep_company(isin)
    else:
        reject_company(isin)  # "Pas assez de data valide"
```

#### **Exemple Réel sur Données**

Titre "ATLASGOLD" :
```
Date        Cours   Gap    Run?
2024-06-15  250.0   -      [1]
2024-06-18  251.5   3j     ✓ → [2]
2024-06-21  249.8   3j     ✓ → [3]
2024-06-25  252.0   4j     ✓ → [4]
2024-07-02  NaN     GAP > 7 ✗ → [RUN BRISÉE, restart 1]
2024-07-05  251.2   3j     ✓ → [2]
2024-07-08  250.5   3j     ✓ → [3]
... etc
```

Résultat: max_consecutive_run = [4] + [next sequence]  
Si aucune séquence ≥ 14, titre REJETÉ.

#### **Alternatives Considérées & Rejetées**

| Approche | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Gap ≤ 7j (CHOIX)** | Capture weekends normaux, rejette données manquantes | Un peu strict | ✅ |
| Gap ≤ 14j | Plus permissif | Accepte 2 semaines manquantes, trop bruyant | ❌ |
| Aucune contrainte gap | Maximal de titres | Indicateurs financièrement faux | ❌ |
| Gap ≤ 3j | Très strict, qualité garantie | 80% des titres rejetés, sample trop petit | ❌ |
| Comptage simple (no gap) | Conceptuel clair | Impossible pour BVC, quasi 0 titres | ❌ |

**Sortie:** `df_universe` avec N titres filtrés (ceux ayant ≥14 obs consécutives, gap ≤7j)

---

### Étape 1 : Indicateurs

**Processus par titre:**
```
Pour chaque CODE_ISIN:
  1. Trier par Date
  2. Pour chaque fenêtre temporelle:
     a. Calculer SMA-20, SMA-50 (strict, min window)
     b. Calculer EMA-20 (dégradé gracieux)
     c. Calculer RSI-14 (Wilder)
     d. Calculer MACD + Signal + Histogram
     e. Calculer RVOL (relative volume)
     f. Calculer VWAP (cumulative)
     g. Calculer HV-20 (annualized)
  3. Pour chaque indicateur, ajouter colonne Valid_Ind ∈ {VALID, INSUFFICIENT_DATA}
```

**Sortie:** DataFrame avec colonnes:
```
[..., SMA_20, SMA_50, EMA_20, RSI_14, MACD, MACD_Signal, MACD_Histogram, 
 RVOL, VWAP, HV_20, Valid_SMA_20, Valid_SMA_50, ..., Valid_HV_20]
```

---

### Étape 2 : Signaux

**Conversion:** indicator_value → signal ∈ {-1, 0, +1, NaN}

**Sortie:** DataFrame avec colonnes:
```
[..., Sig_SMA_20, Sig_SMA_50, Sig_EMA_20, Sig_RSI_14, Sig_MACD, Sig_RVOL, Sig_VWAP]
```

---

### Étape 3 : Familles

**Calcul:** agrégation des signaux par famille

**Sortie:** DataFrame avec colonnes:
```
[..., Score_Tendance, Score_Momentum, Score_Volume]
```

---

### Étape 4 : Score Global & Confiance

**Calcul:** Score_* + coverage + agreement + risk_penalty

**Sortie:** DataFrame avec colonnes:
```
[..., Overall_Score, Confidence]
```

---

### Étape 5 : Décision

**Calcul:** Application des 4 gates

**Sortie:** DataFrame avec colonnes:
```
[..., Recommendation ∈ {BUY, HOLD, SELL, INSUFFICIENT_DATA}]
```

---

## Hypothèses de conception

### Hypothèses Confirmées (Validées)

1. ✅ **7 indicateurs suffisent** : En tests de notebook, pas de gain de performance ajoutant d'autres indicateurs (ATR, Bollinger Bands) sur l'univers MASI
2. ✅ **Séparation Score/Confiance est nécessaire** : Sans elle, faux positifs augmentent en phase volatile
3. ✅ **Signalisation discrète simplifie l'interprétation** : Traders comprennent immédiatement "+1 haussier" sans calculer

### Hypothèses Requérant Validation (Backtesting - Notebook 12)

1. ⚠️ **Poids 35-35-20 sont optimaux**
   - À tester: A(35-35-20), B(30-40-20), C(40-30-20), D(30-30-30), E(40-35-15)
   - Métrique: Hit rate, Sharpe ratio, Max Drawdown sur période dev + validation

2. ⚠️ **Seuils 60/60/40 pour BUY/SELL/Confidence**
   - À tester: Grille {55, 60, 65, 70} pour Score, {50, 60, 70, 80} pour Confidence
   - Métrique: Forward return, risque/rendement

3. ⚠️ **RSI seuils 30/70 adaptés à la BVC**
   - À confirmer: Peut-être que 35/65 marche mieux sur marché moins efficient
   - Métrique: Fréquence des signaux + hit rate

4. ⚠️ **HV > p75 pénalité de 20% est calibrée**
   - À ajuster: Peut-être que p75 est trop bas, ou pénalité trop forte
   - Métrique: Performance en période volatile vs stable

---

## Limitations et pistes d'amélioration

### Limitations Actuelles

#### **L1 : Pas de composante intraday**
```
Problème: Tous les indicateurs utilisent Cours de fermeture
Limitation: Signaux générés APRÈS clôture, trop tard pour scalping
Impact: Horizons d'investissement = swing trading (5-20 jours), pas intraday
Amélioration: Ajouter données intraday (OHLCV par 15min ou 1h) → détail dans Étape 1
```

#### **L2 : Pas de contexte macroéconomique**
```
Problème: Les indicateurs ignorent nouvelles/événements
Limitation: Peut acheter juste avant crash systémique
Impact: Backtesting seulement sur période stable
Amélioration: Intégrer VIX proxy (volatilité implicite) ou calendrier économique
```

#### **L3 : Univers figé à p25 FF_MarketCap**
```
Problème: Threshold absolu (218 M MAD) ne s'adapte pas à liquidité du jour
Limitation: Certains titres inclus aujourd'hui peuvent être illiquides demain
Impact: Slippage élevé sur seuil limite
Amélioration: Dynamiser le filtre via bid-ask spread, turnover actuel
```

#### **L4 : HV basée sur prix, pas sur bid-ask**
```
Problème: HV = écart-type des log-retours de prix fermés
Limitation: Sur marché peu liquide, bid-ask spread = volatilité artificielle
Impact: HV surestimée pour titres illiquides
Amélioration: Calculer realized volatility sur mid-prices, ou utiliser GARCH
```

#### **L5 : Pas de gestion de position**
```
Problème: Moteur produit recommandation, pas de sizing/stop-loss
Limitation: Portfolio manager doit décider de taille position + exit
Impact: Risque non contrôlé
Amélioration: Ajouter module de risk management (ATR-based stops, position sizing)
```

### Pistes d'Amélioration Court-Terme (< 1 mois)

1. **Ajuster poids après backtesting (Notebook 12)**
   - Budget: 5-8 heures
   - Sortie: Rapport des 5 configurations A-E, choix du meilleur

2. **Ajouter visualisation tableau de bord Streamlit**
   - Budget: 4-6 heures
   - Sortie: Vue par titre du détail (indicateurs, signaux, scores, confiance, recommandation)

3. **Implémenter backtester simple (Notebook 12)**
   - Budget: 8-10 heures
   - Sortie: Historique recommandations vs forward returns

### Pistes d'Amélioration Moyen-Terme (1-3 mois)

1. **Machine Learning: Optimiser poids via XGBoost/Random Forest**
   - Données requises: ≥12 mois historical
   - Sortie: Poids appris automatiquement

2. **Ajouter indicateurs alternatifs et comparer**
   - Candidats: Bollinger Bands, ATR, Stochastic, Williams %R
   - Validation: Ajout = amélioration hit rate ?

3. **Intégrer market microstructure data**
   - Données requises: Order book depth, trade sizes
   - Sortie: Indicateurs de liquidité fine

---

## Résumé Visuel du Flux

```
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 0: DONNÉES BRUTES (Cours, Volume, Index Composition)         │
└────────────────────────────┬─────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: 7 INDICATEURS (SMA, EMA, RSI, MACD, RVOL, VWAP, HV)      │
│  ├─ Trend:    SMA-20, SMA-50, EMA-20                                │
│  ├─ Momentum: RSI-14, MACD                                          │
│  ├─ Volume:   RVOL, VWAP                                            │
│  └─ Risk:     HV-20                                                 │
└────────────────────────────┬─────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: SIGNALISATION DISCR. ({+1, 0, -1, NaN})                    │
│ Sig_SMA_20, Sig_SMA_50, Sig_EMA_20, Sig_RSI_14, Sig_MACD,          │
│ Sig_RVOL, Sig_VWAP                                                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: SCORES DE FAMILLE ([0-100])                               │
│ ├─ Score_Tendance   (35%) ← SMA-20, SMA-50, EMA-20                  │
│ ├─ Score_Momentum   (35%) ← RSI-14, MACD                            │
│ └─ Score_Volume     (20%) ← RVOL, VWAP                              │
└────────────────────────────┬─────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4: SCORE GLOBAL & CONFIANCE (INDÉPENDANTS)                    │
│ ├─ Overall_Score    (0-100)   ← Weighted Average Trend/Momentum/Vol │
│ └─ Confidence       (0-100%)  ← Coverage (40%) + Agreement (40%) +   │
│                                  RiskPenalty (20%)                   │
└────────────────────────────┬─────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5: LOGIQUE DE DÉCISION (4 GATES)                              │
│ If Coverage < 50% → INSUFFICIENT_DATA                              │
│ Elif Score ≥ 60 AND Conf ≥ 60% → BUY                               │
│ Elif Score ≤ 40 AND Conf ≥ 60% → SELL                              │
│ Elif 40 < Score < 60 → HOLD                                         │
└────────────────────────────┬─────────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│ RECOMMANDATION FINALE: BUY / HOLD / SELL / INSUFFICIENT_DATA        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

L'architecture du moteur est **intentionnellement simple et explicable**, non pas optimale d'un point de vue ML. Elle privilégie :

✅ **Transparence :** Chaque décision peut être tracée étape par étape  
✅ **Robustesse :** Utilise des indicateurs éprouvés (pas d'expérimentations exotiques)  
✅ **Extensibilité :** Chaque composant (poids, seuils, indicateurs) peut être ajusté séparément  
✅ **Validation :** Hypothesis-driven (baseline → backtesting → production)  

**Point critique :** Ces poids et seuils sont des **hypothèses initiales**, pas des faits scientifiques. Notebook 12 (backtesting) déterminera les vraies valeurs optimales.

---

**Prochaines étapes:**
1. Lancer Notebook 12 (Backtesting) → Valider ou ajuster poids
2. Debug application Streamlit (incoherences actuelles)
3. Une fois poids validés, passer en production

**Contacts & questions :** Section encadrement du rapport

