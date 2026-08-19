"""
Utilitaire de normalisation des codes ISIN.

Les fichiers marché de la BVC exposent parfois le code ISIN sous une forme
bruitée, p.ex. « MA0000012114,XX,CAS » (code + place + segment), alors que le
fichier de composition d'indice fournit un ISIN propre « MA0000012163 ».

Pour que la jointure marché ↔ composition (Gate 1) soit fiable, on isole
UNIQUEMENT le code ISIN normalisé (ex. « MA0000012114 ») des deux côtés.
"""

import re
from typing import Any

# ISIN : 2 lettres pays + 9 à 12 caractères alphanumériques (BVC : MA + 10 chiffres)
_ISIN_RE = re.compile(r'[A-Z]{2}[0-9A-Z]{9,12}')


def looks_like_isin(value: str) -> bool:
    """Vrai si la chaîne ressemble à un ISIN complet (ex. MA0000012114)."""
    if not value:
        return False
    return bool(re.fullmatch(r'[A-Z]{2}[0-9A-Z]{9,12}', value.strip().upper()))


def normalize_isin(value: Any) -> str:
    """
    Extrait le code ISIN propre à partir d'une valeur potentiellement bruitée.

    Exemples
    --------
    'MA0000012114,XX,CAS' -> 'MA0000012114'
    ' ma0000012163 '      -> 'MA0000012163'
    'MA0000012114'        -> 'MA0000012114'
    None / '' / NaN       -> ''
    """
    if value is None:
        return ''
    s = str(value).strip()
    if not s or s.lower() == 'nan':
        return ''

    upper = s.upper()

    # 1) Chercher un motif ISIN à l'intérieur de la chaîne (gère le bruit ',XX,CAS')
    match = _ISIN_RE.search(upper)
    if match:
        return match.group(0)

    # 2) Repli : premier segment avant un séparateur courant
    token = re.split(r'[,;|\s]+', upper)[0].strip()
    return token
