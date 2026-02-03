import pytest
import respx
from httpx import Response
from shwary import Shwary
from shwary.exceptions import ValidationError, AuthenticationError

# --- FIXTURES (Données de test) ---
@pytest.fixture
def client() -> Shwary:
    """Crée un client synchrone pour les tests."""
    return Shwary(
        merchant_id="merchant-test-id",
        merchant_key="merchant-test-key",
        is_sandbox=True
    )


def test_validation_fail_fast(client):
    """Vérifie que le SDK bloque les requêtes invalides localement."""
    # Test numéro invalide
    with pytest.raises(ValidationError) as exc:
        client.initiate_payment("DRC", 5000, "ceci n'est pas un numéro")
    
    # Vérification de la présence d'un mot clé réellement présent dans le message d'erreur
    error_msg = str(exc.value)
    assert "impossible à analyser" in error_msg or "invalide" in error_msg

    # Test montant trop bas pour la RDC
    with pytest.raises(ValidationError) as exc:
        client.initiate_payment("DRC", 100, "+243840000000")
    assert "2900" in str(exc.value)

@respx.mock
def test_initiate_payment_success(client):
    """Simule une réponse 200 OK de l'API Shwary."""
    
    # On définit ce que l'API est censée répondre
    mock_response: dict[str, bool | str] = {
        "id": "trans-123",
        "status": "pending",
        "isSandbox": True
    }
    
    # Interception de la requête POST vers l'URL sandbox
    route = respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/DRC").mock(
        return_value=Response(200, json=mock_response)
    )

    # On initialise la demande de paiement
    response = client.initiate_payment("DRC", 5000, "+243972345678")

    # Vérifications
    assert route.called
    assert response["id"] == "trans-123"
    assert response["status"] == "pending"

@respx.mock
def test_authentication_error(client):
    """Simule une erreur 401 (Mauvaise clé API)."""
    
    respx.post("https://api.shwary.com/api/v1/merchants/payment/sandbox/KE").mock(
        return_value=Response(401, json={"message": "Invalid merchant key"})
    )

    with pytest.raises(AuthenticationError) as exc:
        client.initiate_payment("KE", 1000, "+254700000000")
    
    assert "Invalid merchant key" in str(exc.value)

@respx.mock
def test_get_transaction_success(client):
    """Vérifie la récupération d'une transaction par ID."""
    transaction_id = "c0fdfe50-24be-4de1-9f66-84608fd45a5f"
    
    mock_response: dict[str, int | str] = {
        "id": transaction_id,
        "status": "completed",
        "amount": 5000
    }
    
    # On intercepte le GET
    route = respx.get(f"https://api.shwary.com/api/v1/merchants/transactions/{transaction_id}").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.get_transaction(transaction_id)

    assert route.called
    assert response["id"] == transaction_id
    assert response["status"] == "completed"