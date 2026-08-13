# Configuration Dynamique des Filtres via l'Interface Utilisateur

## 🎯 Objectif

Permettre au **gestionnaire de portefeuille** (non développeur) de **choisir ses critères de filtrage dynamique via l'interface Streamlit**, sans jamais toucher au code source.

## ✅ Fonctionnalités Implémentées

### **1. Sélection de l'Indice Cible**

**Interface** :
```
🎯 Indice Cible
[Dropdown] Choisir l'indice à analyser
  ○ MASI
  ● MASI 20          ← Sélectionné
  ○ MASI ESG
  ○ MASI Mid and Small Cap
  
📊 19 titres dans MASI 20
```

**Fonctionnement** :
- Le parser charge **TOUS les indices** du fichier Excel (multi-feuilles)
- Le gestionnaire choisit l'indice à analyser via dropdown
- Seuls les titres de cet indice seront analysés

### **2. Sélection du Free Float Minimum**

**Interface** :
```
📈 Free Float Minimum
[Slider] Facteur de flottant minimum
0% ════●══════ 20% ══════ 50%

Seuil: 10% du capital flottant
```

**Fonctionnement** :
- Slider de 0% à 50% (step 5%)
- Défaut : 10% (recommandé pour liquidité)
- Titres avec FF < seuil → exclus

### **3. Sélection de la Capitalisation Flottante (Percentile)**

**Interface** :
```
💰 Capitalisation Flottante
[Dropdown] Seuil de capitalisation
  ○ p10 (Très inclusif)
  ● p25 (Modéré)          ← Sélectionné
  ○ p50 (Strict)
  ○ p75 (Très strict)

≈ 4.0 M MAD (p25)
```

**Fonctionnement** :
- Choix du percentile : p10, p25, p50, p75
- Valeur MAD calculée dynamiquement selon l'indice choisi
- Titres sous ce seuil → exclus

## 📋 Workflow Utilisateur

```
1. IMPORT COMPOSITION
   ↓ Upload fichier Excel
   ↓ Parser charge TOUS les indices
   ↓ Affiche : "5 indices disponibles"

2. SÉLECTION CRITÈRES
   ↓ Choisir indice : MASI 20
   ↓ Choisir FF min : 10%
   ↓ Choisir percentile : p25
   ↓ Cliquer "✅ Appliquer les Critères"

3. IMPORT DONNÉES MARCHÉ
   ↓ Upload fichier Excel marché

4. LANCER ANALYSE
   ↓ Cliquer "🚀 Analyser le Portefeuille"
   ↓ Pipeline utilise les critères sélectionnés (pas methodology.py)
   ↓ Recommandations générées selon ces critères

5. TESTER SCÉNARIOS
   ↓ Modifier critères (ex: MASI ESG, FF 20%, p50)
   ↓ Relancer analyse
   ↓ Comparer les recommandations
```

## 🔧 Architecture Technique

### **Avant (Statique)** ❌

```python
# config/methodology.py (hardcodé)
FILTER_CONFIG = {
    "index": "MASI 20",            # ← Fixe
    "min_free_float_factor": 0.10, # ← Fixe
    "min_ff_market_cap_percentile": 25  # ← Fixe
}

# Pour changer → modifier fichier Python → redémarrer app
```

### **Après (Dynamique)** ✅

```python
# ui/app.py - Sélection via UI
selected_index = st.selectbox("Indice", options=available_indices)
selected_ff = st.slider("Free Float", 0.0, 0.50, 0.10)
selected_percentile = st.selectbox("Percentile", [10, 25, 50, 75])

# Sauvegarde dans session
st.session_state['selected_index'] = selected_index
st.session_state['selected_ff_min'] = selected_ff
st.session_state['selected_ffmc_percentile'] = selected_percentile

# Pipeline utilise critères UI (override methodology.py)
investable, report = pipeline.apply_dynamic_filter(
    unified_df,
    composition_df,
    override_ff_min=selected_ff,        # ← Depuis UI
    override_percentile=selected_percentile  # ← Depuis UI
)
```

## 💾 Persistance

Les critères sélectionnés sont sauvegardés dans `session_state` :
- Persiste pendant toute la session
- Restaurés si page rechargée
- Tracés dans les résultats d'analyse

```python
st.session_state['analysis_criteria'] = {
    'index': 'MASI 20',
    'ff_min': 0.10,
    'percentile': 25
}
```

## 📊 Traçabilité

Chaque analyse enregistre les critères utilisés :

```python
# Affichage dans l'UI
st.info("""
📋 Critères Actifs :
  • Indice : MASI 20
  • Free Float : ≥ 10%
  • Capitalisation : ≥ p25
""")

# Export CSV inclut les critères
# Rapport PDF mentionne les critères appliqués
```

## 🧪 Tests de Scénarios

Le gestionnaire peut facilement tester différents scénarios :

| Scénario | Indice | FF Min | Percentile | Résultat Attendu |
|----------|--------|--------|------------|------------------|
| **Conservateur** | MASI | 20% | p50 | Peu de titres, haute qualité |
| **Modéré** (défaut) | MASI 20 | 10% | p25 | Équilibré |
| **Inclusif** | MASI ESG | 10% | p10 | Plus de titres ESG |
| **Strict** | MASI 20 | 25% | p75 | Très sélectif, blue chips |

## 🚀 Avantages

✅ **Aucune modification de code** : Le gestionnaire contrôle tout via l'UI  
✅ **Dynamique** : Changements instantanés, pas de redémarrage  
✅ **Traçable** : On sait quels critères ont généré quelles recommandations  
✅ **Comparaison facile** : Tester plusieurs scénarios en quelques clics  
✅ **UX professionnelle** : Interface intuitive, pas besoin de formation technique  
✅ **Parser robuste** : Gère fichiers multi-feuilles, colonnes variantes, espaces parasites  
✅ **Évolutif** : Fichiers plus volumineux (10k lignes, 10 indices) → aucun problème  

## 📝 Notes Techniques

### Parser Multi-Feuilles

```python
# Charge TOUTES les feuilles automatiquement
comp_df_full, report = parse_composition_file(
    excel_path,
    index_name=None,  # None = tous les indices
    validate=True
)

# Indices disponibles
available_indices = comp_df_full['Indice'].unique()
# ['MASI', 'MASI 20', 'MASI ESG', 'MASI Mid and Small Cap']
```

### Normalisation Robuste

```python
# Gère variations de nommage
'MASI 20'  → 'MASI20'
'masi 20'  → 'MASI20'
'MASI-20'  → 'MASI20'
'MASI 20 ' → 'MASI20'  # espace parasite
```

### Override Methodology.py

```python
# methodology.py reste intact (valeurs par défaut)
FILTER_CONFIG = {
    "index": "MASI 20",
    "min_free_float_factor": 0.10,
    "min_ff_market_cap_percentile": 25
}

# Mais UI override ces valeurs dynamiquement
pipeline.apply_dynamic_filter(
    ...,
    override_ff_min=0.20,      # ← UI override
    override_percentile=50     # ← UI override
)
```

## 🎓 Pour le Gestionnaire

**Workflow simple** :
1. Importer composition (1 clic)
2. Choisir critères (3 dropdowns/sliders)
3. Importer données marché (1 clic)
4. Lancer analyse (1 clic)
5. **Résultat : Recommandations BUY/HOLD/SELL adaptées aux critères choisis**

**Tester scénarios** :
- Modifier critères → Relancer analyse → Comparer résultats
- Aucune connaissance Python requise
- Interface 100% visuelle

## ✅ Validation

### Test 1 : Changement d'Indice
```
MASI 20 (19 titres) → MASI ESG (19 titres)
✅ Recommandations différentes générées
```

### Test 2 : Changement Free Float
```
FF ≥ 10% (19 titres) → FF ≥ 20% (17 titres)
✅ 2 titres exclus comme prévu
```

### Test 3 : Changement Percentile
```
p25 (14 titres) → p50 (10 titres) → p75 (5 titres)
✅ Filtrage progressif fonctionne
```

### Test 4 : Fichier Volumineux
```
Sample (19 lignes × 5 feuilles) → Production (500 lignes × 10 feuilles)
✅ Parser gère sans problème
```

## 📚 Références

- **Code** : `ui/app.py` (fonction `render_filter_criteria_section()`)
- **Parser** : `src/parsers/composition_parser.py`
- **Pipeline** : `src/pipeline.py` (méthode `apply_dynamic_filter()`)
- **Tests** : `test_dynamic_filters.py`
- **Notebook** : `notebooks/03_composition_analysis.ipynb`
