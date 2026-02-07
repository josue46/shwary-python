"""Base client class pour partager la logique commune entre Sync et Async."""

import logging

from shwary import __version__

# Configuration du logger au niveau du module
logger = logging.getLogger("shwary")


class BaseShwaryClient:
    """
    Classe de base pour les clients Shwary (Sync et Async).
    Partage la logique commune : headers, configuration, validation.
    """

    __slots__ = (
        "merchant_id",
        "merchant_key",
        "is_sandbox",
        "_base_url",
        "timeout",
        "logger",
    )

    def __init__(
        self,
        merchant_id: str,
        merchant_key: str,
        is_sandbox: bool = False,
        timeout: float = 30.0,
    ):
        """
        Initialise le client Shwary.

        Args:
            merchant_id: Identifiant du marchand (UUID)
            merchant_key: Clé secrète du marchand
            is_sandbox: Si True, utilise l'environnement de sandbox
            timeout: Timeout global pour les requêtes HTTP (en secondes)
        """
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self.is_sandbox = is_sandbox
        self.timeout = timeout
        self._base_url = "https://api.shwary.com/api/v1/merchants"
        self.logger = logger

    @property
    def headers(self) -> dict[str, str]:
        """Retourne les headers HTTP standardisés pour toutes les requêtes."""
        return {
            "x-merchant-id": self.merchant_id,
            "x-merchant-key": self.merchant_key,
            "Content-Type": "application/json",
            "User-Agent": f"Shwary-Python-SDK/{__version__}",
        }

    def _log_request(self, endpoint: str, json_data: dict) -> None:
        """Enregistre les détails d'une requête (sans données sensibles)."""
        self.logger.debug(
            f"Request: {endpoint}",
            extra={
                "amount": json_data.get("amount"),
                "country": json_data.get("clientPhoneNumber", "")[:5] + "****",
                "is_sandbox": self.is_sandbox,
            },
        )

    def _log_response(
        self, endpoint: str, status_code: int, response_data: dict
    ) -> None:
        """Enregistre les détails d'une réponse."""
        self.logger.debug(
            f"Response: {endpoint} - {status_code}",
            extra={
                "transaction_id": response_data.get("id"),
                "status": response_data.get("status"),
            },
        )

    def _log_error(self, endpoint: str, error: Exception) -> None:
        """Enregistre les détails d'une erreur."""
        self.logger.error(
            f"Request failed: {endpoint}",
            exc_info=True,
            extra={"error_type": type(error).__name__},
        )
