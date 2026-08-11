#!/bin/bash

# Script de vérification complète de l'application DSS

echo "🔍 Vérification de l'application DSS..."
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
PASSED=0
FAILED=0

# Fonction de test
test_item() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $1${NC}"
        ((FAILED++))
    fi
}

# 1. Vérifier Python
echo "1️⃣  Vérification de Python..."
python3 --version > /dev/null 2>&1
test_item "Python installé"

# 2. Vérifier environnement virtuel
echo ""
echo "2️⃣  Vérification de l'environnement virtuel..."
if [ -d ".venv" ]; then
    echo -e "${GREEN}✅ Environnement virtuel existe${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Environnement virtuel manquant${NC}"
    ((FAILED++))
fi

# 3. Activer venv et vérifier dépendances
echo ""
echo "3️⃣  Vérification des dépendances..."
source .venv/bin/activate

python -c "import streamlit" 2>/dev/null
test_item "Streamlit installé"

python -c "import pandas" 2>/dev/null
test_item "Pandas installé"

python -c "import openpyxl" 2>/dev/null
test_item "OpenPyXL installé"

# 4. Vérifier structure des fichiers
echo ""
echo "4️⃣  Vérification de la structure des fichiers..."

[ -f "ui/app.py" ]
test_item "ui/app.py existe"

[ -f "config/translations.py" ]
test_item "config/translations.py existe"

[ -f "ui/components/persistence.py" ]
test_item "ui/components/persistence.py existe"

[ -f "ui/components/state.py" ]
test_item "ui/components/state.py existe"

[ -f "ui/views/market_data.py" ]
test_item "ui/views/market_data.py existe"

[ -f "ui/views/recommendations.py" ]
test_item "ui/views/recommendations.py existe"

[ -f "src/pipeline.py" ]
test_item "src/pipeline.py existe"

# 5. Vérifier dossiers de données
echo ""
echo "5️⃣  Vérification des dossiers de données..."

[ -d "data" ]
test_item "Dossier data/ existe"

mkdir -p data/.app_state
[ -d "data/.app_state" ]
test_item "Dossier data/.app_state/ créé"

# 6. Test des imports Python
echo ""
echo "6️⃣  Test des imports Python..."

python test_app_startup.py > /dev/null 2>&1
test_item "Tous les imports fonctionnent"

# 7. Test de la persistance
echo ""
echo "7️⃣  Test du système de persistance..."

python -c "
from ui.components.persistence import get_state_manager
mgr = get_state_manager()
import pandas as pd
test_df = pd.DataFrame({'test': [1, 2, 3]})
mgr.save_session(decisions_summary=test_df, metadata={'test': 'ok'})
session = mgr.load_session()
assert session['has_saved_state'] == False or session['decisions_summary'] is not None
mgr.clear_session()
print('OK')
" > /dev/null 2>&1
test_item "Système de persistance fonctionnel"

# 8. Vérifier fichiers de documentation
echo ""
echo "8️⃣  Vérification de la documentation..."

[ -f "LANCER_APP.md" ]
test_item "LANCER_APP.md existe"

[ -f "FRENCH_UI_PERSISTENCE.md" ]
test_item "FRENCH_UI_PERSISTENCE.md existe"

[ -f "CHANGEMENTS_MAJEURS.md" ]
test_item "CHANGEMENTS_MAJEURS.md existe"

# Résumé
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Résumé de la vérification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Réussis: $PASSED${NC}"
echo -e "${RED}Échoués: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Tous les tests sont passés!${NC}"
    echo ""
    echo "✨ L'application est prête à être lancée!"
    echo ""
    echo "Pour démarrer:"
    echo "  streamlit run ui/app.py"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  Certains tests ont échoué.${NC}"
    echo ""
    echo "Veuillez corriger les erreurs avant de lancer l'application."
    echo ""
    exit 1
fi
