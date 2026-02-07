import httpx
from tenacity import AsyncRetrying

from ..core import get_retrying_options, prepare_payment_request
from ..exceptions import raise_from_response
from ..schemas import PaymentResponse, TransactionResponse
from .base import BaseShwaryClient


class ShwaryAsync(BaseShwaryClient):
    """
    Client asynchrone haute performance pour l'API Shwary.

    À utiliser dans les applications async (FastAPI, Quart, aiohttp, etc).
    Doit être utilisé comme context manager ou fermé manuellement.

    Exemple:
        async with ShwaryAsync(merchant_id="...", merchant_key="...") as client:
            payment = await client.initiate_payment(
                country="DRC",
                amount=5000,
                phone_number="+243972345678"
            )
    """

    __slots__ = (
        "merchant_id",
        "merchant_key",
        "is_sandbox",
        "_client",
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
        Initialise le client asynchrone Shwary.

        Args:
            merchant_id: Identifiant du marchand (UUID)
            merchant_key: Clé secrète du marchand
            is_sandbox: Si True, utilise l'environnement de sandbox
            timeout: Timeout global pour les requêtes HTTP (en secondes)
        """
        super().__init__(merchant_id, merchant_key, is_sandbox, timeout)
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers=self.headers,
        )

    async def close(self) -> None:
        """Ferme le client HTTP et libère les ressources."""
        await self._client.aclose()
        self.logger.info("ShwaryAsync client closed")

    async def __aenter__(self) -> "ShwaryAsync":
        """Entrée du context manager asynchrone."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Sortie du context manager asynchrone."""
        await self.close()

    async def initiate_payment(
        self,
        country: str,
        amount: float,
        phone_number: str,
        callback_url: str | None = None,
    ) -> PaymentResponse:
        """
        Initie une demande de paiement (asynchrone).

        Avec retry automatique en cas d'erreurs réseau transitoires (timeout, connexion).
        Utilise une stratégie exponentielle: 2s, 4s, 8s... max 10s.

        Args:
            country: Code du pays (DRC, KE, UG)
            amount: Montant de la transaction
            phone_number: Numéro de téléphone au format international
            callback_url: URL de callback optionnelle pour les notifications

        Returns:
            PaymentResponse contenant id, status, isSandbox

        Raises:
            ValidationError: Si les données sont invalides
            AuthenticationError: Si les identifiants sont incorrects
            ShwaryAPIError: Pour tous les autres erreurs API

        Example:
            async with ShwaryAsync(...) as client:
                payment = await client.initiate_payment(
                    country="DRC",
                    amount=5000,
                    phone_number="+243972345678"
                )
                print(f"Transaction ID: {payment['id']}")
        """  # noqa: E501
        endpoint, json_data = prepare_payment_request(
            country, amount, phone_number, callback_url, self.is_sandbox
        )

        self._log_request(endpoint, json_data)

        async for attempt in AsyncRetrying(**get_retrying_options()):
            with attempt:
                try:
                    response = await self._client.post(endpoint, json=json_data)
                    raise_from_response(response)
                    response_dict = response.json()

                    self._log_response(endpoint, response.status_code, response_dict)
                    return PaymentResponse(**response_dict)
                except Exception as e:
                    self._log_error(endpoint, e)
                    raise

    async def get_transaction(self, transaction_id: str) -> TransactionResponse:
        """
        Récupère les détails d'une transaction par son ID (asynchrone).

        Avec retry automatique en cas d'erreurs réseau transitoires.

        Args:
            transaction_id: UUID de la transaction à récupérer

        Returns:
            TransactionResponse contenant id, status, amount, etc.

        Raises:
            ShwaryAPIError: Si la transaction n'existe pas ou erreur API

        Example:
            async with ShwaryAsync(...) as client:
                tx = await client.get_transaction("c0fdfe50-24be-4de1-9f66-84608fd45a5f")
                print(f"Status: {tx['status']}")
        """  # noqa: E501
        endpoint: str = f"/transactions/{transaction_id}"

        self.logger.debug(f"Fetching transaction: {transaction_id}")

        async for attempt in AsyncRetrying(**get_retrying_options()):
            with attempt:
                try:
                    response = await self._client.get(endpoint)
                    raise_from_response(response)
                    response_dict = response.json()

                    self._log_response(endpoint, response.status_code, response_dict)
                    return TransactionResponse(**response_dict)
                except Exception as e:
                    self._log_error(endpoint, e)
                    raise
