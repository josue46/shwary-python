"""Tests complets du client synchrone Shwary."""

import pytest
import respx
from httpx import Response

from shwary import (
    AuthenticationError,
    RateLimitingError,
    Shwary,
    ValidationError,
)
from shwary.schemas import PaymentResponse


# --- FIXTURES ---
@pytest.fixture
def client() -> Shwary:
    """Crée un client synchrone pour les tests."""
    return Shwary(
        merchant_id="550e8400-e29b-41d4-a716-446655440000",
        merchant_key="test-secret-key",
        is_sandbox=True
    )


# --- TEST VALIDATION LOCALE ---

def test_validation_phone_invalid(client):
    """Vérifie que le SDK rejette les numéros invalides localement."""
    with pytest.raises(ValidationError):
        client.initiate_payment("DRC", 5000, "invalid-phone")


def test_validation_amount_too_low_drc(client):
    """Vérifie le montant minimum pour la RDC (2900 CDF)."""
    with pytest.raises(ValidationError) as exc:
        client.initiate_payment("DRC", 100, "+243840000000")
    assert "2900" in str(exc.value)


# --- TEST REQUÊTES RÉUSSIES ---

@respx.mock
def test_initiate_payment_success_drc(client):
    """Simule une initialisation de paiement réussie pour la RDC."""
    mock_response = {"id": "trans-123", "status": "pending", "isSandbox": True}
    
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.initiate_payment("DRC", 5000, "+243972345678")

    assert isinstance(response, PaymentResponse)
    assert response.id == "trans-123"
    assert response.status == "pending"


@respx.mock
def test_initiate_payment_with_callback(client):
    """Vérifie que la callback est bien incluse dans la requête."""
    mock_response = {"id": "trans-cb", "status": "pending", "isSandbox": True}
    
    route = respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    client.initiate_payment(
        "DRC", 5000, "+243972345678",
        callback_url="https://example.com/webhook"
    )

    assert route.called
    request_data = route.calls.last.request.content.decode()
    assert "callbackUrl" in request_data


# --- TEST ERREURS API ---

@respx.mock
def test_authentication_error(client):
    """Simule une erreur 401 (mauvaise clé API)."""
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(401, json={"message": "Invalid merchant key"})
    )

    with pytest.raises(AuthenticationError):
        client.initiate_payment("DRC", 5000, "+243972345678")


@respx.mock
def test_rate_limiting_error(client):
    """Simule une erreur 429 (trop de requêtes)."""
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(429, json={"message": "Rate limited"})
    )

    with pytest.raises(RateLimitingError):
        client.initiate_payment("DRC", 5000, "+243972345678")


# --- TEST GET TRANSACTION ---

@respx.mock
def test_get_transaction_success(client):
    """Vérifie la récupération d'une transaction existante."""
    transaction_id = "c0fdfe50-24be-4de1-9f66-84608fd45a5f"
    mock_response = {"id": transaction_id, "status": "completed", "amount": 5000}
    
    respx.get(f"https://api.shwary.com/api/v1/merchants/transactions/{transaction_id}").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.get_transaction(transaction_id)
    assert response.id == transaction_id
    assert response.status == "completed"


# --- TEST CONTEXT MANAGER ---

@respx.mock
def test_context_manager_close(client):
    """Vérifie que le context manager ferme proprement le client httpx."""
    mock_response = {"id": "trans-123", "status": "pending", "isSandbox": True}
    
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    # Correction : is_sandbox=True pour correspondre à l'URL mockée
    with Shwary(
        merchant_id=client.merchant_id, 
        merchant_key=client.merchant_key,
        is_sandbox=True
    ) as c:
        response = c.initiate_payment("DRC", 5000, "+243972345678")
        assert response.id == "trans-123"
    
    # Correction : accès direct à .is_closed (sans ._state)
    assert c._client.is_closed


# --- TEST PHONE NORMALIZATION ---

@respx.mock
def test_phone_normalization_local_number(client):
    """Vérifie la conversion d'un numéro local (097...) en format international."""
    mock_response = {"id": "trans-norm", "status": "pending", "isSandbox": True}
    
    route = respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    client.initiate_payment("DRC", 5000, "0972345678")

    request_body = route.calls.last.request.content.decode()
    assert "+243972345678" in request_body


# --- TEST PRODUCTION ENDPOINT ---

@respx.mock
def test_production_endpoint(client):
    """Vérifie que l'URL change quand is_sandbox=False."""
    prod_client = Shwary(
        merchant_id=client.merchant_id,
        merchant_key=client.merchant_key,
        is_sandbox=False
    )
    
    mock_response = {"id": "trans-prod", "status": "pending", "isSandbox": False}
    
    # URL sans "/sandbox"
    route = respx.post("https://api.shwary.com/api/v1/merchants/payment/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    prod_client.initiate_payment("DRC", 5000, "+243972345678")
    assert route.called