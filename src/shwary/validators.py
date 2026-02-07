"""
Validateurs additionnels pour le SDK Shwary.

Contient des fonctions utilitaires pour valider les données avant envoi.
"""

import re
from urllib.parse import urlparse

from .schemas import CountryCode


def validate_callback_url(url: str | None) -> bool:
    """
    Valide qu'une URL de callback est bien formée.

    Args:
        url: URL à valider

    Returns:
        True si URL valide, False sinon

    Example:
        validate_callback_url("https://example.com/webhook")  # True
        validate_callback_url("not a url")  # False
    """
    if not url:
        return True  # callback optionnel

    try:
        result = urlparse(url)
        # Doit avoir scheme (http/https) et netloc (domaine)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def validate_merchant_id(merchant_id: str) -> bool:
    """
    Valide le format d'un identifiant marchand.

    Doit être un UUID v4 (format standard).

    Args:
        merchant_id: ID marchand à valider

    Returns:
        True si format valide, False sinon
    """
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(uuid_pattern, merchant_id, re.IGNORECASE))


def validate_transaction_id(transaction_id: str) -> bool:
    """
    Valide le format d'un ID de transaction.

    Doit être un UUID v4 ou un identifiant standard Shwary.

    Args:
        transaction_id: ID transaction à valider

    Returns:
        True si format valide, False sinon
    """
    uuid_pattern = r"^[0-9a-f\-]{32,40}$"
    return bool(re.match(uuid_pattern, transaction_id, re.IGNORECASE))


def validate_amount(amount: float, country: CountryCode) -> tuple[bool, str | None]:
    """
    Valide qu'un montant respecte les règles métier Shwary.

    Args:
        amount: Montant à valider
        country: Pays cible

    Returns:
        Tuple (is_valid, error_message)

    Example:
        is_valid, msg = validate_amount(5000, CountryCode.DRC)
        if not is_valid:
            print(f"Error: {msg}")
    """
    if amount <= 0:
        return False, "Le montant doit être positif"

    min_amounts = {
        CountryCode.DRC: 2900.0,
        CountryCode.KENYA: 1.0,
        CountryCode.UGANDA: 1.0,
    }

    min_amount = min_amounts.get(country, 1.0)

    if amount < min_amount:
        return False, f"Montant minimum pour {country.value}: {min_amount}"

    return True, None
