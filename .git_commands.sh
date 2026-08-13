#!/bin/bash

# Commandes Git pour push initial

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Git Push DSS_CMR sur GitHub"
echo "═══════════════════════════════════════════════════════════════"

# 1. Initialiser repo
git init

# 2. Ajouter tous les fichiers (sauf .gitignore)
git add .

# 3. Premier commit
git commit -m "feat: Initial commit - DSS CMR v2.2 (Coverage Graceful)"

# 4. Renommer branche en main
git branch -M main

# 5. Ajouter remote
git remote add origin https://github.com/boumhandkhalid-pixel/DSS_CMR.git

# 6. Push
git push -u origin main

echo ""
echo "✅ Push terminé !"
echo "📍 Repository: https://github.com/boumhandkhalid-pixel/DSS_CMR"

