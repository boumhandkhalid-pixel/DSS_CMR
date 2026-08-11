# 🚀 Guide de Lancement - Application DSS

## Démarrage Rapide

### 1. Activer l'environnement virtuel
```bash
cd /home/yass/Desktop/DSS_CMR
source .venv/bin/activate
```

### 2. Lancer l'application Streamlit
```bash
streamlit run ui/app.py
```

### 3. Ouvrir dans le navigateur
L'application s'ouvrira automatiquement à: **http://localhost:8501**

---

## ✨ Nouvelles Fonctionnalités

### 🇫🇷 Interface Entièrement en Français
- Tous les textes sont en français
- Les termes techniques restent en anglais (MASI, RSI, MACD, spread, bid, ask)
- Navigation intuitive en français

### 💾 Persistance Automatique
- **Les données persistent au rafraîchissement de page!**
- Plus besoin de re-télécharger les fichiers
- L'état est sauvegardé automatiquement

### 🗂️ Pages Disponibles
1. **Tableau de Bord** - Vue d'ensemble
2. **Données Marché** - Import des données Excel
3. **Métriques Marché** - Statistiques détaillées
4. **Composition Indice** - Import composition MASI/MADEX
5. **Analyse** - Analyses techniques
6. **Recommandations** - Décisions ACHAT/CONSERVER/VENDRE
7. **Paramètres** - Configuration

---

## 📊 Workflow Typique

### Première Utilisation

1. **Ouvrir la page "Données Marché"**
   - Télécharger le fichier Excel du marché
   - Cliquer sur "🔄 Parser & Valider"
   - Vérifier le rapport de validation

2. **Ouvrir la page "Composition Indice"**
   - Télécharger le fichier de composition
   - Valider l'import

3. **Ouvrir la page "Analyse"**
   - Cliquer sur "🚀 Lancer le Pipeline Complet"
   - Attendre le traitement

4. **Consulter les "Recommandations"**
   - Voir les décisions ACHAT/CONSERVER/VENDRE
   - Exporter en CSV/JSON/Parquet

### Utilisations Suivantes

**C'est là que la magie opère!** 🎉

- Rafraîchissez la page (F5) → **Tout est encore là!**
- Fermez l'onglet → Rouvrez → **Les données persistent!**
- Redémarrez l'app → **Session restaurée automatiquement!**

---

## 🔧 Gestion de Session

### Sidebar (Barre Latérale)

La sidebar affiche:
- ✅/❌ Statut des données marché
- ✅/❌ Statut de la composition indice
- ✅/❌ Statut du pipeline
- 💾 Date de dernière sauvegarde

### Boutons de Gestion

- **🗑️ Effacer** - Efface complètement la session
- **♻️ Recharger** - Force le rechargement depuis la sauvegarde

---

## 📁 Structure de Sauvegarde

Les données sont sauvegardées dans:
```
data/.app_state/
├── unified_data.parquet          # Données marché
├── composition_data.parquet      # Composition indices
├── decisions_summary.parquet     # Décisions finales
└── metadata.json                 # Métadonnées
```

**Note**: Ces fichiers sont créés automatiquement, ne pas modifier manuellement.

---

## 🎯 Décisions d'Investissement

### Traductions des Décisions

| Anglais | Français |
|---------|----------|
| BUY | ACHAT |
| HOLD | CONSERVER |
| SELL | VENDRE |
| INSUFFICIENT_DATA | DONNÉES INSUFFISANTES |

### Codes Couleur

- 🟢 **ACHAT** - Vert (opportunité d'achat)
- 🟡 **CONSERVER** - Jaune (maintenir position)
- 🔴 **VENDRE** - Rouge (vendre)
- ⚪ **DONNÉES INSUFFISANTES** - Gris (pas assez de données)

---

## 🔍 Filtres et Export

### Filtres Disponibles
- Type de décision (ACHAT/CONSERVER/VENDRE)
- Confiance minimale (0-100%)
- Score minimal (0-100)

### Formats d'Export
- **CSV** - Compatible Excel
- **JSON** - Pour intégrations API
- **Parquet** - Format haute performance

---

## ⚠️ Notes Importantes

### 1. Avertissement Méthodologie
Les décisions utilisent des **poids hypothétiques**.

**Ne PAS utiliser pour du trading réel** tant que le backtesting (Notebook 12) n'est pas terminé.

### 2. Données Échantillon
Les données échantillon ont seulement 14-28 sessions.

En production (6-12 mois de données):
- Plus de signaux ACHAT/VENDRE
- Indicateurs techniques valides
- Confiance améliorée

### 3. Termes Techniques
Ces termes restent EN ANGLAIS comme demandé:
- Indices: MASI, MADEX
- Indicateurs: RSI, SMA, EMA, MACD, RVOL, VWAP
- Finance: spread, bid, ask
- Formats: Parquet, Excel

---

## 🐛 Dépannage

### L'app ne démarre pas
```bash
# Vérifier l'environnement virtuel
source .venv/bin/activate

# Vérifier les dépendances
pip install -r requirements.txt

# Tester les imports
python test_app_startup.py
```

### Les données ne persistent pas
```bash
# Vérifier le dossier de sauvegarde
ls -la data/.app_state/

# Si vide, re-télécharger les données
```

### Erreur "applymap"
✅ **Déjà corrigé!** Utilisez `map()` (pandas 2.1+)

### Erreur "File is not a zip file"
✅ **Déjà corrigé!** Utilisez `engine='openpyxl'` et `.getvalue()`

---

## 📚 Documentation

- **FRENCH_UI_PERSISTENCE.md** - Détails techniques complets
- **QUICKSTART.md** - Guide rapide original
- **README.md** - Vue d'ensemble du projet
- **PIPELINE_STATUS.md** - État du pipeline

---

## 🎉 Fonctionnalités Clés

✅ **Interface 100% Française**
✅ **Persistance Automatique**
✅ **Import Excel → Parquet**
✅ **Pipeline DSS Complet**
✅ **Décisions Colorées**
✅ **Export Multi-Format**
✅ **Sidebar Interactive**
✅ **Restauration Auto**

---

## 💡 Conseils d'Utilisation

1. **Première fois**: Suivez le workflow dans l'ordre (Marché → Indice → Pipeline → Recommandations)

2. **Sessions suivantes**: Juste ouvrir l'app, tout est déjà là!

3. **Tests rapides**: Utilisez les fichiers dans `samples/`

4. **Production**: Utilisez les fichiers officiels BVC

5. **Dépannage**: Cliquez "🗑️ Effacer" pour repartir de zéro

---

## 🚀 Bon Trading!

Pour des questions ou problèmes:
- Consultez FRENCH_UI_PERSISTENCE.md
- Vérifiez les logs de l'app
- Testez avec `python test_app_startup.py`

**L'application est prête à l'emploi!** 🎊
