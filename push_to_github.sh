#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "🚀 Push DSS_CMR sur GitHub"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Étape 1: Push branche dev
echo "📤 Étape 1: Push de la branche dev..."
git push -u origin dev

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du push de dev"
    exit 1
fi

echo "✅ Branche dev pushée avec succès"
echo ""

# Étape 2: Créer et push la branche main
echo "📤 Étape 2: Création et push de la branche main..."
git checkout -b main 2>/dev/null || git checkout main
git merge dev --no-edit
git push -u origin main

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du push de main"
    exit 1
fi

echo "✅ Branche main pushée avec succès"
echo ""

# Retour sur dev
git checkout dev

echo "═══════════════════════════════════════════════════════════════"
echo "✅ PUSH TERMINÉ AVEC SUCCÈS !"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📍 Repository: https://github.com/boumhandkhalid-pixel/DSS_CMR"
echo ""
echo "Branches pushées:"
echo "  ✅ dev  (branche de développement)"
echo "  ✅ main (branche principale)"
echo ""
echo "Pour voir le repo sur GitHub:"
echo "  https://github.com/boumhandkhalid-pixel/DSS_CMR"
echo ""
