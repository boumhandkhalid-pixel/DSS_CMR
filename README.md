# DSS CMR - Système d'Aide à la Décision pour Gestion de Portefeuille

**Decision Support System pour la Caisse Marocaine des Retraites**

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Proprietary-yellow.svg)]()

---

## 📋 Description

**DSS CMR** est un système d'aide à la décision développé pour le pôle Gestion de Portefeuille de la Caisse Marocaine des Retraites (CMR). Il fournit des recommandations d'investissement automatisées basées sur l'analyse technique et fondamentale des titres de la Bourse des Valeurs de Casablanca (BVC).

### 🎯 Objectifs

- **Automatiser l'analyse technique** de titres boursiers marocains
- **Générer des recommandations** BUY/HOLD/SELL basées sur 7 indicateurs techniques
- **Filtrer l'univers investissable** selon les critères CMR (MASI, Free Float, Market Cap)
- **Fournir une interface intuitive** pour les gestionnaires de portefeuille

### ⚡ Fonctionnalités Principales

- ✅ **Import dynamique** de fichiers Excel (données marché + composition d'indice)
- ✅ **Pipeline d'analyse en 6 étapes** (filtrage, indicateurs, signaux, décision)
- ✅ **7 indicateurs techniques** : SMA-20, SMA-50, EMA-20, RSI-14, MACD, RVOL, VWAP
- ✅ **Coverage Graceful** : utilise les données disponibles (pas de rejet si < 50 obs)
- ✅ **Score & Confidence** indépendants pour décision robuste
- ✅ **Interface Streamlit** en français avec design institutionnel CMR
- ✅ **Export CSV** des recommandations
- ✅ **Persistance automatique** des sessions

---

## 🏗️ Architecture

Le système repose sur une architecture en **6 étapes** :

```
ÉTAPE 0: Import & Filtrage
    ↓ Données Excel → Univers investissable (MASI, FF≥20%, p25)
ÉTAPE 1: Indicateurs Techniques
    ↓ Calcul de 7 indicateurs (SMA, EMA, RSI, MACD, RVOL, VWAP, HV)
ÉTAPE 2: Signalisation
    ↓ Conversion en signaux discrets (+1/0/-1/NaN)
ÉTAPE 3: Scores par Famille
    ↓ Agrégation en 3 familles (Trend 35%, Momentum 35%, Volume 20%)
ÉTAPE 4: Score Global & Confidence
    ↓ Overall_Score [0-100] + Confidence [0-100%]
ÉTAPE 5: Décision
    ↓ BUY / HOLD / SELL / INSUFFICIENT_DATA
```

### 📐 Principe Fondamental : **Coverage Graceful**

Contrairement aux systèmes classiques qui rejettent un titre si `observations < 50`, DSS CMR adopte une approche flexible :

- **Ancien système** : Titre 30 obs → ❌ Rejeté → 0 indicateurs
- **DSS CMR** : Titre 30 obs → ✅ Conservé → 7/8 indicateurs valides (87% coverage)

Chaque indicateur gère son propre minimum :
- RSI-14 : 15 observations
- SMA-20 : 20 observations
- SMA-50 : 50 observations

Si un titre a 30 observations continues, **SMA-50 sera NaN** mais **RSI-14, SMA-20, etc. fonctionneront**. La décision finale s'adapte au coverage disponible.

---

## 🚀 Installation

### Prérequis

- Python 3.14+
- pip ou conda
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

---

## 🎮 Lancement de l'Application

### Interface Streamlit

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Lancer l'application
streamlit run ui/app.py
```

L'application s'ouvre automatiquement dans le navigateur à l'adresse : **http://localhost:8501**

### Workflow Utilisateur

1. **Import des données**
   - Importer le fichier Excel **Données Marché** (cours, volume, etc.)
   - Importer le fichier Excel **Composition d'Indice** (MASI, Free Float, etc.)

2. **Sélection de l'indice**
   - Choisir l'indice de référence (MASI par défaut)

3. **Analyse**
   - Cliquer sur **"Analyser le Portefeuille"**
   - Le pipeline s'exécute automatiquement (6 étapes)
   - Progress bar en temps réel

4. **Résultats**
   - Tableau récapitulatif : Titre, Score, Confidence, Décision
   - Filtres : BUY / HOLD / SELL
   - Export CSV disponible

5. **Réinitialiser**
   - Bouton **"Réinitialiser"** pour nouvelle analyse

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

**Exemple :**
```
Date       | CODE_ISIN      | Company           | Cours  | Bid    | Ask    | Volume MC | Quantité MC
2026-07-01 | MA0000012632   | ATTIJARIWAFA BANK | 525.00 | 524.50 | 525.50 | 12500     | 23810
```

### Fichier 2 : Composition d'Indice

**Colonnes requises :**
- `Indice` : Nom de l'indice (MASI, MASI 20, MASI ESG, etc.)
- `CODE_ISIN` : Code ISIN du titre
- `FF` : Free Float Factor [0-1]
- `FF_MarketCap` : Capitalisation flottante (MAD)
- `Weight` : Poids dans l'indice [0-1]
- `Nb titres` : Nombre de titres

**Exemple :**
```
Indice | CODE_ISIN      | FF   | FF_MarketCap | Weight | Nb titres
MASI   | MA0000012632   | 0.45 | 5200000000   | 0.18   | 100000000
```

---

## 🧪 Tests

### Tests Unitaires

```bash
# Lancer tous les tests
pytest tests/ -v

# Test end-to-end du pipeline
pytest tests/test_e2e_pipeline.py -v

# Test avec couverture
pytest tests/ --cov=src --cov-report=html
```

### Notebooks de Validation

Les notebooks dans `notebooks/` permettent de valider chaque étape du pipeline :

- `00_pipeline_test.ipynb` : Test complet du pipeline
- `09_technical_indicators.ipynb` : Validation des indicateurs
- `10_business_rules.ipynb` : Validation des règles métier
- `11_decision_engine.ipynb` : Validation du moteur de décision

---

## 📁 Structure du Projet

```
DSS_CMR/
├── config/
│   ├── methodology.py          # Configuration méthodologique (poids, seuils)
│   ├── settings.py             # Configuration application
│   └── translations.py         # Traductions français
├── src/
│   ├── ingestion.py            # Import et parsing Excel
│   ├── validation.py           # Filtres qualité et dynamiques
│   ├── indicators.py           # Calcul des 7 indicateurs
│   ├── signals.py              # Signalisation et scores
│   ├── decisions.py            # Moteur de décision
│   ├── metrics.py              # Métriques de marché
│   ├── pipeline.py             # Orchestration du pipeline
│   ├── normalization/          # Normalisation des données
│   └── parsers/                # Parsers Excel adaptatifs
├── ui/
│   ├── app.py                  # Interface Streamlit principale
│   ├── components/             # Composants réutilisables (state, persistence)
│   └── assets/                 # CSS, logos
├── tests/
│   └── test_e2e_pipeline.py    # Tests end-to-end
├── notebooks/                   # Notebooks de validation
├── .gitignore                   # Exclusions Git
├── requirements.txt             # Dépendances Python
├── ARCHITECTURE_ESSENTIALS.md   # Documentation architecture détaillée
├── COVERAGE_GRACEFUL_IMPLEMENTATION.md  # Documentation Coverage Graceful
└── README.md                    # Ce fichier
```

---

## 🔧 Configuration

### Paramètres Méthodologiques

Tous les paramètres sont centralisés dans `config/methodology.py` :

**Filtrage dynamique :**
```python
FILTER_CONFIG = {
    "index": "MASI",                      # Indice de référence
    "min_free_float_factor": 0.20,        # FF minimum (20%)
    "min_ff_market_cap_percentile": 25,   # p25 de la capitalisation flottante
}
```

**Indicateurs techniques :**
```python
INDICATOR_PARAMS = {
    "sma_short": 20,    # SMA court terme
    "sma_long": 50,     # SMA long terme
    "rsi_period": 14,   # Période RSI
    "macd_fast": 12,    # MACD rapide
    "macd_slow": 26,    # MACD lent
    # ...
}
```

**Poids des familles :**
```python
SCORE_WEIGHTS = {
    "Trend": 0.35,      # 35% Tendance
    "Momentum": 0.35,   # 35% Momentum
    "Volume": 0.20,     # 20% Volume
    "Risk": 0.10,       # 10% Risque (Confidence)
}
```

**Seuils de décision :**
```python
DECISION_THRESHOLDS = {
    "buy": {"min_score": 60, "min_confidence": 60},   # BUY si Score≥60 ET Conf≥60
    "sell": {"max_score": 40, "min_confidence": 60},  # SELL si Score≤40 ET Conf≥60
}
```

---

## 📖 Documentation Technique

### Documents disponibles

- **`ARCHITECTURE_ESSENTIALS.md`** : Architecture détaillée du moteur de décision (6 étapes, formules mathématiques, rationale)
- **`COVERAGE_GRACEFUL_IMPLEMENTATION.md`** : Implémentation de l'approche Coverage Graceful
- **`GUIDE_TEST_RAPIDE.md`** : Guide de test rapide de l'application

### Méthodologie

Le système utilise une approche **hypothesis-driven** :

1. **Baseline Hypothesis** : Les poids 35-35-20 et seuils 60/40 sont des hypothèses initiales
2. **Backtesting requis** : Validation empirique via Notebook 12 (à venir)
3. **Itération** : Ajustement des paramètres selon performance historique

⚠️ **Important** : Les poids actuels ne sont **PAS validés empiriquement**. Ils représentent une baseline raisonnable basée sur l'expertise métier.

---

## 🤝 Contribution

### Workflow Git

```bash
# 1. Créer une branche feature
git checkout -b feature/nom-de-la-feature

# 2. Faire les modifications
# ... éditer fichiers ...

# 3. Commiter
git add .
git commit -m "feat: description de la feature"

# 4. Pousser
git push origin feature/nom-de-la-feature

# 5. Créer une Pull Request sur GitHub
```

### Conventions de commit

- `feat:` Nouvelle fonctionnalité
- `fix:` Correction de bug
- `docs:` Documentation
- `refactor:` Refactoring sans changement fonctionnel
- `test:` Ajout/modification de tests
- `chore:` Maintenance (dépendances, config, etc.)

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

## 🔮 Roadmap

### MVP (Actuel)
- ✅ Pipeline complet (6 étapes)
- ✅ Interface Streamlit fonctionnelle
- ✅ Export CSV
- ✅ Coverage Graceful
- ✅ Persistance sessions

### Phase 2 (Q3 2026)
- [ ] Backtesting historique (Notebook 12)
- [ ] Validation empirique des poids
- [ ] Optimisation hyperparamètres
- [ ] Ajout indicateurs alternatifs (Bollinger, ATR, Stochastic)

### Phase 3 (Q4 2026)
- [ ] API REST pour intégration
- [ ] Données intraday (15min, 1h)
- [ ] Machine Learning (XGBoost pour poids automatiques)
- [ ] Market microstructure data (order book)

### Production (2027)
- [ ] Connexion live à la BVC
- [ ] Alertes temps réel
- [ ] Module risk management (stop-loss, position sizing)
- [ ] Intégration VIX proxy (volatilité implicite)

---

**Version** : 2.2 (Coverage Graceful)  
**Dernière mise à jour** : 13 août 2026
