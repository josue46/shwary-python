"""Tests pour les retries automatiques et la gestion des erreurs réseau."""

import time

import pytest
import respx
from httpx import ConnectError, Response, TimeoutException

from shwary import Shwary, ShwaryAPIError, ShwaryAsync, ValidationError

# --- LOGIQUE DE RETRY ---
# 

class TestSyncRetries:
    """Tests pour les retries du client synchrone."""

    @pytest.fixture
    def client(self):
        """Crée un client synchrone pour les tests de retry."""
        return Shwary(
            merchant_id="test-id",
            merchant_key="test-key",
            is_sandbox=True,
            timeout=5.0,
        )

    @respx.mock
    def test_retry_on_timeout(self, client):
        """Vérifie que le client échoue après épuisement des retries sur timeout."""
        respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
            side_effect=TimeoutException("Request timeout")
        )

        start_time = time.time()

        # Doit lever TimeoutException si reraise=True dans tenacity
        with pytest.raises(TimeoutException):
            client.initiate_payment("DRC", 5000, "+243972345678")

        elapsed = time.time() - start_time
        # Correction de l'assertion : 3 attempts (0s, ~1s, ~2s) = env 3s minimum
        assert elapsed >= 3

    @respx.mock
    def test_retry_succeeds_on_second_attempt(self, client):
        """Vérifie qu'une réussite en 2e tentative fonctionne."""
        mock_response = {"id": "trans-123", "status": "pending", "isSandbox": True}

        route = respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC")
        route.side_effect = [
            ConnectError("Connection failed"),
            Response(200, json=mock_response),
        ]

        response = client.initiate_payment("DRC", 5000, "+243972345678")

        assert response.id == "trans-123"
        assert route.call_count == 2

    def test_no_retry_on_validation_error(self, client):
        """Vérifie que les erreurs de validation ne sont pas retentées (immédiat)."""
        with pytest.raises(ValidationError):
            client.initiate_payment("DRC", -1, "+243972345678")


class TestAsyncRetries:
    """Tests pour les retries du client asynchrone."""

    @pytest.fixture
    def async_client(self):
        return ShwaryAsync(
            merchant_id="test-id",
            merchant_key="test-key",
            is_sandbox=True
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_async_retry_on_connect_error(self, async_client):
        """Vérifie les retries asynchrones en cas de ConnectError."""
        respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
            side_effect=ConnectError("Connection refused")
        )

        with pytest.raises(ConnectError):
            async with async_client as c:
                await c.initiate_payment("DRC", 5000, "+243972345678")


class TestErrorDetails:
    """Tests pour la richesse des données d'erreur."""

    @pytest.fixture
    def client(self):
        return Shwary(merchant_id="test-id", merchant_key="test-key", is_sandbox=True)

    @respx.mock
    def test_api_error_preserves_response(self, client):
        """Vérifie que ShwaryAPIError contient les détails du serveur."""
        error_data = {
            "message": "Transaction failed",
            "code": "INSUFFICIENT_FUNDS",
            "details": {"amount": 5000, "balance": 1000},
        }

        respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
            return_value=Response(400, json=error_data)
        )

        with pytest.raises(ShwaryAPIError) as exc:
            client.initiate_payment("DRC", 5000, "+243972345678")
        
        assert exc.value.status_code == 400
        assert exc.value.raw_response["code"] == "INSUFFICIENT_FUNDS"


class TestClientCleanup:
    """Vérifie que les ressources HTTP sont libérées."""

    def test_sync_client_context_manager(self):
        """Vérifie la fermeture automatique (Sync)."""
        with Shwary(merchant_id="test-id", merchant_key="test-key") as client:
            assert not client._client.is_closed
        
        # Correction : is_closed doit être True
        assert client._client.is_closed

    @pytest.mark.asyncio
    async def test_async_client_context_manager(self):
        """Vérifie la fermeture automatique (Async)."""
        async with ShwaryAsync(merchant_id="test-id", merchant_key="test-key") as client:
            assert not client._client.is_closed
            
        assert client._client.is_closed


class TestLogging:
    """Vérifie l'intégration du système de logs."""

    def test_configure_logging_available(self):
        from shwary import configure_logging
        assert callable(configure_logging)

    def test_logger_exists(self):
        import logging
        logger = logging.getLogger("shwary")
        assert logger.name == "shwary"