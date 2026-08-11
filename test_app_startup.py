"""
Test de démarrage de l'application Streamlit.

Vérifie que tous les imports fonctionnent et que l'app peut démarrer.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

print("🔍 Test des imports...")

# Test imports principaux
try:
    import streamlit as st
    print("✅ Streamlit OK")
except ImportError as e:
    print(f"❌ Streamlit: {e}")
    sys.exit(1)

try:
    from ui.app import main
    print("✅ ui.app OK")
except ImportError as e:
    print(f"❌ ui.app: {e}")
    sys.exit(1)

try:
    from config.translations import PAGE_TITLES, TITLES, BUTTONS, MESSAGES
    print("✅ config.translations OK")
    print(f"   Pages: {list(PAGE_TITLES.values())[:3]}...")
except ImportError as e:
    print(f"❌ config.translations: {e}")
    sys.exit(1)

try:
    from ui.components.persistence import get_state_manager
    print("✅ ui.components.persistence OK")
except ImportError as e:
    print(f"❌ ui.components.persistence: {e}")
    sys.exit(1)

try:
    from ui.components.state import init_session_state, save_session_state
    print("✅ ui.components.state OK")
except ImportError as e:
    print(f"❌ ui.components.state: {e}")
    sys.exit(1)

try:
    # sidebar supprimé - application minimaliste
    print("✅ sidebar supprimé (interface minimaliste)")
except ImportError as e:
    print(f"⚠ sidebar supprimé (OK pour interface minimaliste)")

try:
    from ui.views.market_data import render as render_market_data
    print("✅ ui.views.market_data OK")
except ImportError as e:
    print(f"❌ ui.views.market_data: {e}")
    sys.exit(1)

try:
    from ui.views.recommendations import render as render_recommendations
    print("✅ ui.views.recommendations OK")
except ImportError as e:
    print(f"❌ ui.views.recommendations: {e}")
    sys.exit(1)

try:
    from src.pipeline import DSS_Pipeline
    print("✅ src.pipeline OK")
except ImportError as e:
    print(f"❌ src.pipeline: {e}")
    sys.exit(1)

print("\n🎉 Tous les imports réussis!")
print("\n📋 Résumé des traductions:")
print(f"   - Pages: {len(PAGE_TITLES)} traductions")
print(f"   - Titres: {len(TITLES)} traductions")
print(f"   - Boutons: {len(BUTTONS)} traductions")
print(f"   - Messages: {len(MESSAGES)} traductions")

print("\n🚀 L'application est prête à démarrer!")
print("\nPour lancer l'app:")
print("   cd /home/yass/Desktop/DSS_CMR")
print("   source .venv/bin/activate")
print("   streamlit run ui/app.py")
