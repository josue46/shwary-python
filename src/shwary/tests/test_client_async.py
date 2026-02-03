import pytest
import respx
from httpx import Response
from shwary import ShwaryAsync

@pytest.fixture
def async_client() -> ShwaryAsync:
    """Crée un client asynchrone pour les tests."""
    return ShwaryAsync(
        merchant_id="merchant-test-id",
        merchant_key="merchant-test-key",
        is_sandbox=True
    )

@pytest.mark.asyncio
@respx.mock
async def test_async_payment_success(async_client):
    """Vérifie que le client Async fonctionne aussi."""
    
    mock_response: dict[str, str] = {"id": "async-123", "status": "completed"}
    
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/UG").mock(
        return_value=Response(200, json=mock_response)
    )

    # Notez l'utilisation de 'async with' et 'await'
    async with async_client as c:
        response = await c.initiate_payment("UG", 5000, "+256700000000")

    assert response["id"] == "async-123"