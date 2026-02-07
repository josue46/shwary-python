"""Tests complets du client asynchrone ShwaryAsync."""

import asyncio

import httpx
import pytest
import respx
from httpx import Response

from shwary import (
    AuthenticationError,
    ShwaryAsync,
    ValidationError,
)
from shwary.schemas import PaymentResponse


# --- FIXTURES ---
@pytest.fixture
def async_client() -> ShwaryAsync:
    """Crée un client asynchrone pour les tests."""
    return ShwaryAsync(
        merchant_id="550e8400-e29b-41d4-a716-446655440000",
        merchant_key="test-secret-key",
        is_sandbox=True,
    )


# --- TEST VALIDATION LOCALE ---


@pytest.mark.asyncio
async def test_async_validation_phone_invalid(async_client):
    """Vérifie la validation du numéro en mode async (doit être awaité)."""
    with pytest.raises(ValidationError):
        # CORRECTION : initiate_payment est asynchrone, il faut l'awaiter
        # pour que l'exception soit capturée correctement par pytest.raises
        await async_client.initiate_payment("DRC", 5000, "invalid")


# --- TEST REQUÊTES RÉUSSIES ---


@pytest.mark.asyncio
@respx.mock
async def test_async_payment_success_drc(async_client):
    """Simule une initialisation de paiement asynchrone réussie pour la RDC."""
    mock_response = {"id": "async-trans-123", "status": "pending", "isSandbox": True}

    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    async with async_client as c:
        response = await c.initiate_payment("DRC", 5000, "+243972345678")

    assert isinstance(response, PaymentResponse)
    assert response.id == "async-trans-123"


@pytest.mark.asyncio
@respx.mock
async def test_async_payment_with_callback(async_client):
    """Vérifie que le callback est inclus dans le corps de la requête."""
    mock_response = {"id": "async-trans-cb", "status": "pending", "isSandbox": True}

    route = respx.post(
        "https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC"
    ).mock(return_value=Response(200, json=mock_response))

    async with async_client as c:
        await c.initiate_payment(
            "DRC", 5000, "+243972345678", callback_url="https://example.com/webhook"
        )

    # Vérifie que le JSON envoyé contient bien callbackUrl
    request_data = route.calls.last.request.content.decode()
    assert "callbackUrl" in request_data


# --- TEST ERREURS ---


@pytest.mark.asyncio
@respx.mock
async def test_async_authentication_error(async_client):
    """Simule une erreur 401."""
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(401, json={"message": "Invalid merchant key"})
    )

    async with async_client as c:
        with pytest.raises(AuthenticationError):
            await c.initiate_payment("DRC", 5000, "+243972345678")


# --- TEST CONTEXT MANAGER ASYNC ---


@pytest.mark.asyncio
@respx.mock
async def test_async_context_manager_close():
    """Vérifie que le client httpx interne est bien fermé."""
    client = ShwaryAsync(
        merchant_id="550e8400-e29b-41d4-a716-446655440000",
        merchant_key="test-key",
        is_sandbox=True,
    )

    async with client as c:
        assert not c._client.is_closed

    # CORRECTION : On accède à .is_closed directement sur le client
    assert client._client.is_closed


# --- TEST RETRY MECHANISM ---


@pytest.mark.asyncio
@respx.mock
async def test_async_retry_on_timeout(async_client):
    """Vérifie le mécanisme de retry sur erreur transitoire."""
    mock_success = {"id": "retry-success", "status": "pending", "isSandbox": True}

    # Simulation : 1er appel échoue (Timeout), 2ème appel réussit
    _ = respx.post(
        "https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC"
    ).side_effect = [
        httpx.TimeoutException("Connect timeout"),
        Response(200, json=mock_success),
    ]

    async with async_client as c:
        # Si reraise=True est configuré dans tenacity, ceci passera au 2ème essai
        response = await c.initiate_payment("DRC", 5000, "+243972345678")

    assert response.id == "retry-success"


# --- TEST PARALLEL PAYMENTS ---


@pytest.mark.asyncio
@respx.mock
async def test_async_parallel_payments(async_client):
    """Teste la capacité à gérer plusieurs requêtes simultanées."""
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(
            200, json={"id": "p1", "status": "pending", "isSandbox": True}
        )
    )
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/KE").mock(
        return_value=Response(
            200, json={"id": "p2", "status": "pending", "isSandbox": True}
        )
    )
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/UG").mock(
        return_value=Response(
            200, json={"id": "p3", "status": "pending", "isSandbox": True}
        )
    )

    async with async_client as c:
        # On lance les trois en même temps
        results = await asyncio.gather(
            c.initiate_payment("DRC", 5000, "+243972345678"),
            c.initiate_payment("KE", 10, "+254700000000"),
            c.initiate_payment("UG", 50, "+256700000000"),
        )

    assert results[0].id == "p1"
    assert results[1].id == "p2"
    assert results[2].id == "p3"
