"""
Shwary Python SDK - Client moderne pour l'API de paiement Shwary.

Permet d'initier des paiements Mobile Money en RDC, Kenya et Ouganda
avec validation stricte et gestion d'erreurs complète.

Exemple d'utilisation:
    from shwary import Shwary

    with Shwary(merchant_id="...", merchant_key="...") as client:
        payment = client.initiate_payment(
            country="DRC",
            amount=5000,
            phone_number="+243972345678"
        )
        print(f"Transaction: {payment['id']}")
"""

# Configure le logging au premier import
# Importe les autres modules
from .__version__ import __version__  # noqa: F401
from .clients import Shwary, ShwaryAsync
from .exceptions import (
    AuthenticationError,
    InsufficientFundsError,
    RateLimitingError,
    ShwaryAPIError,
    ShwaryError,
    ValidationError,
)
from .logging_config import configure_logging
from .schemas import (
    CountryCode,
    PaymentResponse,
    TransactionResponse,
    WebhookPayload,
)

__all__ = [
    # Clients
    "Shwary",
    "ShwaryAsync",
    # Exceptions
    "ShwaryError",
    "ValidationError",
    "AuthenticationError",
    "InsufficientFundsError",
    "RateLimitingError",
    "ShwaryAPIError",
    # Schemas
    "CountryCode",
    "PaymentResponse",
    "TransactionResponse",
    "WebhookPayload",
    # Logging
    "configure_logging",
]
