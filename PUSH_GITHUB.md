# Guide de Push vers GitHub

Ce fichier contient les commandes pour pousser le code nettoyé vers GitHub.

## Prérequis

- Avoir un dépôt GitHub créé (ex: `https://github.com/boumhandkhalid-pixel/DSS_CMR.git`)
- Authentification Git configurée (token ou SSH)

## Commandes

```bash
# 1. Vérifier l'état du dépôt local
cd /home/yass/Desktop/DSS_CMR
git status

# 2. Vérifier que le remote est configuré (si premier push)
git remote -v
# Si pas de remote ou mauvaise URL :
# git remote add origin https://github.com/boumhandkhalid-pixel/DSS_CMR.git
# OU pour SSH :
# git remote add origin git@github.com:boumhandkhalid-pixel/DSS_CMR.git

# 3. Pousser vers GitHub (branche main ou master selon la config du dépôt distant)
git push -u origin main
# OU si la branche distante s'appelle 'master' :
# git push -u origin master

# 4. Vérifier sur GitHub que tout est bien poussé
# Aller sur https://github.com/boumhandkhalid-pixel/DSS_CMR
```

## Ce qui a été nettoyé (commit précédent)

✅ **Supprimé** :
- Fichiers `.md` redondants (ARCHITECTURE_ESSENTIALS, COVERAGE_GRACEFUL_IMPLEMENTATION, DYNAMIC_FILTERS_UI, GUIDE_TEST_RAPIDE, PRESENTATION, ANALYSE_TECHNIQUE)
- Scripts `.sh` (push_to_github.sh, run_tests.sh, .git_commands.sh, verifier_app.sh)
- Tests temporaires à la racine (test_app_startup.py, test_dynamic_filters.py, test_traductions.py, diagnose_market_file.py)
- Gros fichier Excel déplacé dans `samples/` (ignoré par Git)

✅ **Conservé** :
- Code source structuré : `src/`, `config/`, `ui/`, `tests/`
- `README.md` (mis à jour Flash Momentum v3.0)
- `requirements.txt` (dépendances)
- `main.tex` (rapport LaTeX)
- `.gitignore` (exclut automatiquement `data/`, `samples/`, `notebooks/`, caches, logs)

✅ **Ignoré par Git** (ne sera jamais poussé) :
- `data/` (fichiers `.parquet` générés automatiquement au lancement)
- `samples/` (fichiers Excel de test)
- `notebooks/` (fichiers `.ipynb`)
- `__pycache__/` et `*.pyc`
- `.venv/` (environnement virtuel)
- `*.log` (logs)

## Après le push

Quelqu'un qui clone le dépôt devra :

1. Installer les dépendances :
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Importer ses propres fichiers Excel dans l'interface Streamlit (le DSS les demandera au premier lancement).

3. Lancer l'application :
   ```bash
   streamlit run ui/app.py
   ```

Les dossiers `data/`, `samples/`, `.pytest_cache/` et les fichiers `.parquet` seront créés automatiquement au premier lancement.

---

**Version du dépôt** : 3.0 (Flash Momentum + Troncature Segment Continu Récent)  
**Date de nettoyage** : 20 août 2026
