"""
Traductions français pour l'interface utilisateur DSS.

Tous les textes de l'interface sont en français.
Les termes techniques anglais (MASI, RSI, MACD, spread, etc.) restent inchangés.
"""

# Titres de pages
PAGE_TITLES = {
    'Dashboard': 'Tableau de Bord',
    'Market Data': 'Données Marché',
    'Market Metrics': 'Métriques Marché',
    'Index Composition': 'Composition Indice',
    'Analysis': 'Analyse',
    'Recommendations': 'Recommandations',
    'Settings': 'Paramètres'
}

# Titres et sous-titres
TITLES = {
    'app_title': 'BVC Portfolio DSS',
    'app_subtitle': 'Données marché, filtrage et recommandations',
    'market_data_title': 'Données Marché',
    'market_data_caption': 'Téléchargez le classeur officiel du marché (Excel) — conversion automatique en Parquet pour un traitement rapide.',
    'market_metrics_title': 'Métriques Marché',
    'market_metrics_caption': 'Calculer et analyser les métriques marché essentielles pour la prise de décision de portefeuille.',
    'index_composition_title': 'Composition Indice',
    'index_composition_caption': 'Téléchargez le classeur de composition des indices (Excel) — conversion automatique en Parquet.',
    'analysis_title': 'Analyse',
    'analysis_caption': 'Exécutez le pipeline d\'analyse une fois que les deux datasets sont disponibles.',
    'recommendations_title': 'Recommandations',
    'recommendations_caption': 'Consultez les décisions finales ACHAT / CONSERVER / VENDRE générées par le pipeline DSS complet.',
    'settings_title': 'Paramètres',
    'settings_caption': 'Configurer les indicateurs futurs, filtres et règles sans changer la structure de l\'interface.',
}

# Boutons
BUTTONS = {
    'parse_validate': '🔄 Parser & Valider',
    'run_pipeline': '🚀 Lancer le Pipeline Complet',
    'apply_filters': 'Appliquer les Filtres',
    'download_csv': 'Télécharger CSV',
    'download_json': 'Télécharger JSON',
    'download_parquet': 'Télécharger Parquet',
    'clear_session': '🗑️ Effacer la Session',
    'restore_session': '♻️ Restaurer la Session',
    'save_settings': '💾 Sauvegarder les Paramètres',
    'reset_settings': '🔄 Réinitialiser',
    'run_analysis': '🚀 Lancer l\'Analyse de Portefeuille',
    'rerun_analysis': '🔄 Relancer l\'Analyse',
}

# Messages
MESSAGES = {
    'upload_info': '👆 Téléchargez un fichier Excel pour commencer le traitement.',
    'processing': 'Traitement du fichier Excel...',
    'success_excel': '✅ Excel traité avec succès → `{path}`',
    'error_import': '❌ Échec de l\'importation: {error}',
    'error_details': '📋 Détails de l\'erreur',
    'pipeline_ready': '✅ Les données marché et la composition de l\'indice sont prêtes!',
    'pipeline_complete': '✅ Pipeline terminé! Allez à la page **Recommandations** pour voir les décisions.',
    'no_decisions': '⚠️ Aucune décision disponible. Veuillez télécharger les données marché et la composition de l\'indice, puis lancer le pipeline.',
    'no_recommendations': 'Aucune recommandation disponible. Lancez d\'abord le pipeline.',
    'running_pipeline': '🔄 Exécution du pipeline DSS...',
    'insufficient_data_note': 'Normal avec les données échantillon (seulement 14-28 sessions). En production avec 6-12 mois de données, plus de signaux ACHAT/VENDRE se déclencheront.',
    'session_restored': '♻️ Session restaurée depuis la sauvegarde',
    'session_cleared': '🗑️ Session effacée',
    'analysis_complete': '✅ Analyse terminée! Consultez la page **Recommandations** pour voir les décisions.',
    'analysis_failed': '❌ Échec de l\'analyse: {error}',
    'computing_metrics': 'Calcul des métriques marché...',
    'settings_saved': '✅ Paramètres sauvegardés pour la session courante.',
}

# Labels de métriques
METRICS = {
    'sheets_included': 'Feuilles Incluses',
    'total_records': 'Enregistrements Totaux',
    'companies': 'Sociétés',
    'sessions': 'Sessions',
    'variables': 'Variables',
    'index': 'Indice',
    'total_securities': 'Titres Totaux',
    'columns': 'Colonnes',
    'buy_signals': 'Signaux ACHAT',
    'hold_signals': 'Signaux CONSERVER',
    'sell_signals': 'Signaux VENDRE',
    'insufficient_data': 'Données Insuffisantes',
    'decision': 'Décision',
    'overall_score': 'Score Global',
    'confidence': 'Confiance',
    'latest_price': 'Dernier Cours',
    'data_coverage': 'Couverture Données',
    'metrics_computed': 'Métriques Calculées',
    'metrics_skipped': 'Métriques Ignorées',
    'warnings': 'Avertissements',
    'companies_analyzed': 'Sociétés Analysées',
}

# Décisions
DECISIONS = {
    'BUY': 'ACHAT',
    'HOLD': 'CONSERVER',
    'SELL': 'VENDRE',
    'INSUFFICIENT_DATA': 'DONNÉES INSUFFISANTES'
}

# Onglets
TABS = {
    'ingestion_report': '📋 Rapport d\'Ingestion',
    'data_quality': '✓ Qualité des Données',
    'preview': '📊 Aperçu',
    'included_sheets': '✓ Feuilles Incluses',
    'excluded_sheets': '⊗ Feuilles Exclues',
}

# Colonnes de tableaux
TABLE_COLUMNS = {
    'CODE_ISIN': 'CODE ISIN',
    'Company': 'Société',
    'Decision': 'Décision',
    'Overall_Score': 'Score',
    'Confidence': 'Confiance',
    'Data_Coverage': 'Couverture',
    'Cours': 'Cours',
    'Date': 'Date',
    'Signals': 'Signaux',
    'Sheet': 'Feuille',
    'Variable': 'Variable',
    'Records': 'Enregistrements',
    'Reason': 'Raison',
}

# Sections
SECTIONS = {
    'prerequisites': '📊 Prérequis',
    'next_steps': '🚀 Prochaines Étapes',
    'investment_decisions': '📋 Décisions d\'Investissement',
    'filter_recommendations': '🔍 Filtrer les Recommandations',
    'export_decisions': '📥 Exporter les Décisions',
    'decision_evidence': '📊 Justification de la Décision',
    'summary_statistics': '📈 Statistiques Résumées',
    'data_completeness': '🔍 Complétude des Données',
    'composition_preview': '📊 Aperçu de la Composition',
    'top_10_weight': '🏢 Top 10 par Poids',
    'validation_report': 'Rapport de Validation',
    'dataset_preview': 'Aperçu du Dataset',
}

# Filtres
FILTERS = {
    'decision_type': 'Type de Décision',
    'min_confidence': 'Confiance Minimale %',
    'min_score': 'Score Minimal',
}

# Étapes du pipeline
PIPELINE_STAGES = {
    'quality_filter': 'Application du filtre qualité...',
    'dynamic_filter': 'Application du filtre d\'investissabilité dynamique...',
    'indicators': 'Calcul des indicateurs techniques...',
    'signals': 'Calcul des signaux et scores...',
    'decisions': 'Génération des décisions d\'investissement...',
}

# Avertissements
WARNINGS = {
    'methodology_not_validated': """
    ⚠️ **IMPORTANT**: Ces décisions utilisent des poids et seuils **HYPOTHÈSE DE RÉFÉRENCE**.
    
    La méthodologie n'a PAS encore été validée via backtesting historique.
    
    N'utilisez PAS ces recommandations pour des transactions réelles tant que le Notebook 12 (Backtesting Historique)
    n'a pas confirmé que la stratégie produit des rendements ajustés au risque positifs.
    
    **Statut**: Pipeline validé ✅ | Méthodologie validée ❌
    """,
    'sample_data_limitation': """
    Les données échantillon ont seulement 14-28 sessions par société.
    En production avec 6-12 mois de données, les indicateurs seront VALIDES et les signaux ACHAT/VENDRE se déclencheront.
    """,
    'upload_both_files': '⚠️ Téléchargez à la fois les données marché et la composition de l\'indice pour lancer le pipeline.',
}

# Instructions
INSTRUCTIONS = {
    'market_data_steps': """
1. **Données Marché** téléchargées et validées
2. **Composition Indice** téléchargée
3. **Pipeline** exécuté
""",
    'next_steps_guide': """
1. Allez à la page **Données Marché**
2. Téléchargez le fichier Excel
3. Allez à la page **Composition Indice**
4. Téléchargez le fichier de composition
5. Revenez ici pour lancer le pipeline
""",
}

# Aide (help text)
HELP_TEXT = {
    'buy_signals': 'Sociétés recommandées à l\'achat',
    'hold_signals': 'Sociétés à conserver en position actuelle',
    'sell_signals': 'Sociétés recommandées à la vente',
    'insufficient_data': 'Sociétés avec données incomplètes',
}

# Termes techniques (restent en anglais)
TECHNICAL_TERMS = [
    'MASI', 'RSI', 'SMA', 'EMA', 'MACD', 'RVOL', 'VWAP', 'HV',
    'spread', 'bid', 'ask', 'Parquet', 'Excel'
]
