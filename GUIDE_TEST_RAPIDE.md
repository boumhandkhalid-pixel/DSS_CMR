# Guide de Test Rapide - BVC Portfolio DSS

## 🚀 Lancement

```bash
cd /home/yass/Desktop/DSS_CMR
source .venv/bin/activate
streamlit run ui/app.py
```

Ouvrir: **http://localhost:8501**

---

## ✅ Test 1: Interface Propre au Démarrage

**Attentes:**
- [x] Titre "BVC Portfolio DSS" visible
- [x] 3 sections: (1) Données, (2) Analyse, (3) Recommandations
- [x] Aucun message de succès parasite
- [x] Aucune erreur dans la console
- [x] Logo bien positionné (si présent)

**Si problème:**
- Vérifier que `st.set_page_config()` est bien la première ligne
- Vérifier les imports

---

## ✅ Test 2: Import Données Marché

**Actions:**
1. Cliquer sur "Browse files" dans colonne gauche
2. Sélectionner fichier: `data/Données Marché Boursier_Projet_IA.xlsx`
3. Cliquer sur bouton **"Importer"**

**Attentes:**
- [x] Spinner "Import en cours..." s'affiche
- [x] Message "✓ Marché importé: X sociétés" apparaît
- [x] Statut change: "✓ Marché"
- [x] Nom du fichier s'affiche
- [x] Nombre de sociétés et enregistrements affiché

**Si erreur:**
- Lire le message d'erreur
- Cliquer sur "Détails" pour voir le traceback
- Vérifier que le fichier Excel est valide

---

## ✅ Test 3: Import Composition Indices

**Actions:**
1. Cliquer sur "Browse files" dans colonne droite
2. Sélectionner fichier: `data/Compo_All_Indices_20260731.xlsx`
3. Cliquer sur bouton **"Importer"**

**Attentes:**
- [x] Spinner "Import en cours..." s'affiche
- [x] Message "✓ Composition importée: X titres" apparaît
- [x] Statut change: "✓ Composition"
- [x] Nom du fichier s'affiche
- [x] Nombre de titres affiché
- [x] Statut global: "✓ Prêt"

---

## ✅ Test 4: Lancement de l'Analyse

**Actions:**
1. Vérifier que statut est "✓ Prêt"
2. Cliquer sur **"Analyser le portefeuille"** (bouton bleu)

**Attentes:**
- [x] Message "⚠ Analyse en cours..." apparaît
- [x] Progress bar avec 7 étapes s'affiche:
  ```
  ○ Normalisation
  ● Contrôle qualité  ← étape actuelle
  ○ Métriques
  ○ Filtrage
  ○ Indicateurs
  ○ Signaux
  ○ Décisions
  ```
- [x] Les ✓ remplacent les ○ au fur et à mesure
- [x] Message final "✓ Analyse terminée"
- [x] Bouton change en "Relancer l'analyse"

**Durée attendue:** 5-15 secondes

---

## ✅ Test 5: Visualisation des Recommandations

**Attentes:**
- [x] Section 3 se remplit automatiquement
- [x] 4 métriques affichées:
  ```
  ACHAT    CONSERVER    VENDRE    INSUFFISANT
    X          Y          Z           W
  ```
- [x] Tableau avec colonnes:
  - Société
  - Score
  - Confiance
  - Décision (colorée)
- [x] Couleurs correctes:
  - ACHAT = vert
  - CONSERVER = jaune
  - VENDRE = rouge
  - INSUFFISANT = gris

---

## ✅ Test 6: Export CSV

**Actions:**
1. Cliquer sur **"Exporter en CSV"**

**Attentes:**
- [x] Fichier `recommandations.csv` téléchargé
- [x] Fichier s'ouvre dans Excel/LibreOffice
- [x] Données cohérentes avec le tableau

---

## ✅ Test 7: Détails d'une Société

**Actions:**
1. Sélectionner une société dans le dropdown
2. Observer les détails affichés

**Attentes:**
- [x] 3 métriques affichées:
  - Décision
  - Score/100
  - Confiance%
- [x] Liste de signaux (si disponibles)
- [x] Expander "Informations supplémentaires" cliquable

---

## ✅ Test 8: Refresh de Page (Persistance)

**Actions:**
1. Après avoir terminé l'analyse
2. Appuyer sur **F5** (refresh)

**Attentes:**
- [x] Données marché toujours présentes
- [x] Composition toujours présente
- [x] Recommandations toujours affichées
- [x] Aucune perte de données

---

## ✅ Test 9: Relancer l'Analyse

**Actions:**
1. Cliquer sur **"Relancer l'analyse"**

**Attentes:**
- [x] Analyse redémarre
- [x] Progress bar s'affiche à nouveau
- [x] Résultats mis à jour

---

## ✅ Test 10: Gestion d'Erreurs

**Test A: Fichier Invalide**
1. Uploader un fichier .txt renommé en .xlsx
2. Cliquer "Importer"

**Attentes:**
- [x] Message d'erreur explicite
- [x] Expander "Détails" avec traceback
- [x] Application reste stable

**Test B: Analyse Sans Données**
1. Au démarrage (pas de fichiers)
2. Observer section "2. Analyse"

**Attentes:**
- [x] Message "ℹ Importez les deux fichiers pour lancer l'analyse"
- [x] Pas de bouton "Analyser" cliquable

---

## 🎯 Résumé des Tests

| Test | Description | Statut |
|------|-------------|--------|
| 1 | Interface propre | ✓ |
| 2 | Import marché | ✓ |
| 3 | Import composition | ✓ |
| 4 | Lancement analyse | ✓ |
| 5 | Visualisation | ✓ |
| 6 | Export CSV | ✓ |
| 7 | Détails société | ✓ |
| 8 | Persistance | ✓ |
| 9 | Relancer analyse | ✓ |
| 10 | Gestion erreurs | ✓ |

---

## 🐛 Troubleshooting

### Erreur: "File is not a zip file"
**Cause:** Fichier Excel corrompu ou format incorrect  
**Solution:** Réessayer avec le fichier original

### Erreur: "No module named 'src'"
**Cause:** Environnement virtuel pas activé  
**Solution:** `source .venv/bin/activate`

### Données pas sauvegardées après refresh
**Cause:** Problème de persistance  
**Solution:** Vérifier que `data/.app_state/` existe

### Progress bar ne s'affiche pas
**Cause:** Analyse trop rapide  
**Solution:** Normal si données échantillon

### Aucune recommandation affichée
**Cause:** Données insuffisantes  
**Solution:** Normal avec échantillon 14-28 sessions

---

## 📊 Résultats Attendus (Données Échantillon)

Avec les fichiers fournis:
- **Sociétés**: ~14 sociétés
- **Sessions**: 14-28 sessions par société
- **Recommandations**:
  - ACHAT: 0-3
  - CONSERVER: 3-7
  - VENDRE: 0-2
  - INSUFFISANT: 5-10

**Note:** Beaucoup de "INSUFFISANT" est normal avec peu de sessions.  
En production (6-12 mois): plus de signaux ACHAT/VENDRE.

---

## ✅ Application Validée

Si tous les tests passent:
- ✅ Interface robuste et intuitive
- ✅ Workflow opérationnel
- ✅ Gestion d'erreurs fonctionnelle
- ✅ Persistance active
- ✅ Export CSV OK

**L'application est prête pour utilisation!** 🎉
