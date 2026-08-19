# DSS CMR - Système d'Aide à la Décision pour Gestion de Portefeuille

**Decision Support System pour la Caisse Marocaine des Retraites**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)]()

---

## 📋 Description

**DSS CMR** est un système d'aide à la décision développé pour le pôle Gestion de Portefeuille de la Caisse Marocaine des Retraites (CMR). Il fournit des recommandations d'investissement automatisées (BUY/HOLD/SELL) basées sur l'**analyse technique Flash Momentum** des titres de la Bourse des Valeurs de Casablanca (BVC).

### 🎯 Objectifs

- **Automatiser l'analyse technique** de titres boursiers marocains via le score Flash Momentum (0–100)
- **Générer des recommandations** BUY/HOLD/SELL basées sur **8 indicateurs techniques** (RVOL, OBV, RSI, SMA-20/50/200, MACD + Signal)
- **Filtrer l'univers investissable** selon les critères CMR (MASI, Free Float ≥20%, p25 capitalisation flottante)
- **Fournir une interface intuitive** pour les gestionnaires de portefeuille avec traçabilité complète

### ⚡ Fonctionnalités Principales

- ✅ **Import dynamique** de fichiers Excel (données marché + composition d'indice)
- ✅ **Pipeline d'analyse robuste** avec contrôle qualité et troncature au segment continu récent
- ✅ **Score Flash Momentum (0–100)** : agrégation de 4 piliers (Volume /20, Momentum /25, Tendance /35, MACD /20)
- ✅ **Coverage Graceful** : indicateurs calculés selon l'historique disponible (pas de rejet brutal)
- ✅ **Traçabilité complète** : d'où viennent les titres (marché, indice, jointure, contrôle qualité)
- ✅ **Interface Streamlit** en français avec design institutionnel CMR
- ✅ **Export CSV** des recommandations + persistance automatique des sessions
- ✅ **Légende explicite** des classes de score (+++ / ++ / + / - / --)

---

## 🏗️ Architecture

Le système repose sur un **pipeline en 6 étapes** :

```
ÉTAPE 0 : Import & Filtrage Dynamique
    ↓ Données Excel → Univers investissable (MASI, FF≥20%, p25 capitalisation flottante)
    ↓ Contrôle qualité temporelle (troncature au segment continu récent si trou > 7j)

ÉTAPE 1 : Indicateurs Techniques
    ↓ Calcul de 8 indicateurs : RVOL, OBV, RSI-14, SMA-20/50/200, MACD, MACD-Signal
    ↓ Chaque indicateur gère son propre minimum d'observations (15–200)

ÉTAPE 2 : Scoring Flash Momentum
    ↓ Agrégation en 4 piliers (déterministes, pas de poids arbitraires) :
        • Volume (RVOL + tendance OBV) ......... 20 points
        • Momentum (RSI-14) .................... 25 points
        • Tendance (SMA + alignement + Golden Cross) ... 35 points
        • MACD (croisement & signe) ............ 20 points
    ↓ Technical Score [0–100]

ÉTAPE 3 : Classification
    ↓ 80–100 → +++ (Très Fort) · 60–79 → ++ (Modéré à Positif)
    ↓ 40–59 → + / - (Neutre) · 0–39 → -- (Faible / Baissier)

ÉTAPE 4 : Décision Finale
    ↓ BUY (score ≥60) / HOLD (40–59) / SELL (score <40) / INSUFFICIENT_DATA (couverture <seuil)
```

### 📐 Principe Fondamental : **Coverage Graceful + Troncature au Segment Continu Récent**

#### Coverage Graceful

Contrairement aux systèmes classiques qui rejettent un titre si `observations < 200`, DSS CMR adopte une approche flexible :

- **Ancien système** : Titre 30 obs → ❌ Rejeté → 0 indicateurs → INSUFFICIENT_DATA forcé
- **DSS CMR** : Titre 30 obs → ✅ Conservé → 6/8 indicateurs valides (SMA-50/200 absents) → couverture 75% → HOLD ou BUY possible selon les 6 indicateurs disponibles

Chaque indicateur gère son propre minimum :

- RSI-14 : 15 observations
- SMA-20 : 20 observations
- SMA-50 : 50 observations
- SMA-200 : 200 observations

Si un titre a 30 observations continues, **SMA-50 et SMA-200 seront NaN** (couverture réduite), mais **RVOL, OBV, RSI-14, SMA-20, MACD fonctionneront**. Le score s'adapte aux indicateurs disponibles.

#### Troncature au Segment Continu Récent

Un **trou ancien** (ex. suspension de cotation il y a 3 ans) ne fait **plus perdre** toute la société :

- **Ancienne logique** : Titre avec écart de 21 jours (2019) → ❌ Rejeté → perte du titre malgré 1800 cours valides 2020–2026
- **Nouvelle logique** : Titre avec écart de 21 jours (2019) → ✅ Conservé → on **garde uniquement** le segment continu 2020–2026 (aucun écart >7j à l'intérieur) → titre analysable avec son historique récent

Seule exception : une société n'est retirée que si elle n'a **aucun cours valide**.

---

## 🚀 Installation

### Prérequis

- Python 3.10+
- pip
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/boumhandkhalid-pixel/DSS_CMR.git
cd DSS_CMR

# 2. Créer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Sur Windows: .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Vérifier l'installation
python3 -c "import streamlit; import pandas; import numpy; print('✅ Installation OK')"
```

**Les fichiers temporaires** (`.parquet`, `__pycache__`, logs) **seront créés automatiquement** au premier lancement.

---

## 🎮 Lancement de l'Application

### Interface Streamlit

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer l'application (port par défaut : 8501)
streamlit run ui/app.py
```

L'application s'ouvre automatiquement dans le navigateur à l'adresse : **http://localhost:8501**

### Workflow Utilisateur

1. **Import des données**
   - Importer le fichier Excel **Données Marché** (cours, volume, etc.)
   - Importer le fichier Excel **Composition d'Indice** (MASI, Free Float, poids, etc.)

2. **Sélection de l'indice**
   - Choisir l'indice de référence (MASI ou MASI 20)

3. **Analyse**
   - Cliquer sur **"Analyser le Portefeuille"**
   - Le pipeline s'exécute automatiquement (6 étapes)
   - Progress bar en temps réel

4. **Résultats**
   - **Tableau récapitulatif** : Société, Score Technique, Classe (+++ / ++ / + / - / --), Couverture, Décision
   - **Filtres** : BUY / HOLD / SELL
   - **Détails par société** : piliers (Volume, RSI, MM, MACD), indicateurs individuels, couverture X/8
   - **Traçabilité** : d'où viennent les titres (marché, indice, jointure, motifs de rejet)
   - **Export CSV** disponible

5. **Réinitialiser**
   - Bouton **"Réinitialiser"** pour nouvelle analyse (efface session + fichiers temporaires)

---

## 📊 Format des Fichiers d'Entrée

### Fichier 1 : Données Marché

**Colonnes requises :**

- `Date` : Date de l'observation (format YYYY-MM-DD)
- `CODE_ISIN` : Code ISIN du titre (ex: MA0000012632)
- `Company` : Nom de la société
- `Cours` : Cours de clôture
- `Bid` : Prix d'achat
- `Ask` : Prix de vente
- `Volume MC` : Volume échangé (en milliers MAD)
- `Quantité MC` : Quantité échangée

### Fichier 2 : Composition d'Indice

**Colonnes requises :**

- `Indice` : Nom de l'indice (MASI, MASI 20, MASI ESG, etc.)
- `CODE_ISIN` : Code ISIN du titre
- `FF` : Free Float Factor [0-1]
- `FF_MarketCap` : Capitalisation flottante (MAD)
- `Weight` : Poids dans l'indice [0-1]
- `Nb titres` : Nombre de titres

---

## 🧪 Tests

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer tous les tests
pytest tests/ -v

# Test end-to-end du pipeline
pytest tests/test_e2e_pipeline.py -v
```

Les tests sont exécutés automatiquement au premier lancement (`pytest` disponible dans `requirements.txt`).

---

## 📁 Structure du Projet

```
DSS_CMR/
├── config/
│   ├── methodology.py          # Configuration Flash Momentum (piliers, seuils, couverture)
│   ├── settings.py             # Configuration application
│   └── translations.py         # Traductions français
├── src/
│   ├── ingestion.py            # Import et parsing Excel
│   ├── validation.py           # Contrôle qualité + troncature segment continu récent
│   ├── indicators.py           # Calcul des 8 indicateurs (RVOL, OBV, RSI, SMA, MACD)
│   ├── scoring_flash.py        # Score Flash Momentum (4 piliers, 0–100)
│   ├── decisions.py            # Moteur de décision (BUY/HOLD/SELL)
│   ├── traceability.py         # Trace par société (couverture, table indicateurs)
│   ├── metrics.py              # Métriques de marché
│   ├── pipeline.py             # Orchestration du pipeline complet
│   ├── normalization/          # Normalisation des données
│   └── parsers/                # Parsers Excel adaptatifs
├── ui/
│   ├── app.py                  # Interface Streamlit principale
│   ├── components/             # Composants réutilisables (state, persistence)
│   └── assets/                 # CSS, logos
├── tests/
│   ├── test_e2e_pipeline.py    # Test end-to-end complet
│   └── test_flash_scoring.py   # Test unitaire scoring Flash Momentum
├── notebooks/                   # Notebooks de validation (ignorés par Git)
├── data/                        # Fichiers temporaires (*.parquet) — ignorés par Git
├── .gitignore                   # Exclusions Git (caches, data/, logs)
├── requirements.txt             # Dépendances Python
├── main.tex                     # Rapport LaTeX
└── README.md                    # Ce fichier
```

---

## 🔧 Configuration

Tous les paramètres sont centralisés dans `config/methodology.py` :

### Filtrage dynamique

```python
FILTER_CONFIG = {
    "index": "MASI",
    "min_free_float_factor": 0.20,
    "min_ff_market_cap_percentile": 25,
}
```

### Score Flash Momentum (4 piliers)

```python
FLASH_MOMENTUM_CONFIG = {
    # Pilier Volume (20 pts) = RVOL (10) + tendance OBV (10)
    "volume": {...},
    # Pilier RSI (25 pts) : 55–70 → 25, 45–55 → 15, >70 → 10, <30 → 0
    "rsi": {...},
    # Pilier Moyennes Mobiles (35 pts) = position + alignement + Golden Cross
    "ma": {...},
    # Pilier MACD (20 pts) : 4 états (croisement ET signe)
    "macd": {...},
    # Classification : 80–100 (+++)  · 60–79 (++)  · 40–59 (+ / -)  · 0–39 (--)
    "classification": [...],
    # Inputs requis pour la couverture (8 indicateurs)
    "coverage_inputs": ["RVOL", "OBV", "RSI_14", "SMA_20", "SMA_50", "SMA_200", "MACD", "MACD_Signal"],
}
```

### Seuils de décision

```python
FLASH_DECISION_THRESHOLDS = {
    "buy_min_score":  60,   # Score ≥ 60 → BUY
    "sell_max_score": 40,   # Score < 40 → SELL
    # Entre 40 et 60 → HOLD
}

MIN_COVERAGE_FOR_DECISION = 0.5   # Couverture < 50% (4/8 indicateurs) → INSUFFICIENT_DATA
```

---

## 📜 License

**Proprietary** - © 2026 Caisse Marocaine des Retraites (CMR)

Ce projet est la propriété exclusive de la CMR. Toute utilisation, reproduction ou distribution non autorisée est strictement interdite.

---

## 👥 Auteurs

**Équipe Projet DSS CMR**

- Pôle Gestion de Portefeuille - Caisse Marocaine des Retraites
- Développement : 2026

---

## 📞 Contact

Pour toute question ou support :

- **Email** : gestion.portefeuille@cmr.gov.ma
- **Organisation** : Caisse Marocaine des Retraites (CMR)

---

**Version** : 3.0 (Flash Momentum + Troncature Segment Continu Récent)  
**Dernière mise à jour** : 18 août 2026
