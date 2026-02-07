"""Tests des modèles Pydantic (schemas)."""

from datetime import datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from shwary.schemas import (
    CountryCode,
    PaymentPayload,
    PaymentResponse,
    TransactionResponse,
    WebhookPayload,
)


class TestCountryCode:
    """Tests de l'énumération CountryCode."""
    
    def test_valid_country_codes(self):
        """Teste que les codes de pays valides existent."""
        assert CountryCode.DRC == "DRC"
        assert CountryCode.KENYA == "KE"
        assert CountryCode.UGANDA == "UG"
    
    def test_invalid_country_code(self):
        """Teste qu'un code invalide lève une exception."""
        with pytest.raises(ValueError):
            CountryCode("INVALID")


class TestPaymentPayload:
    """Tests du modèle PaymentPayload."""
    
    def test_valid_payload_drc(self):
        """Teste la création d'un payload valide pour la RDC."""
        payload = PaymentPayload(
            amount=5000,
            clientPhoneNumber="+243972345678",
            callbackUrl="https://example.com/webhook",
            country_target=CountryCode.DRC,
        )
        
        assert payload.amount == 5000
        assert payload.clientPhoneNumber == "+243972345678"
        assert payload.country_target == CountryCode.DRC
    
    def test_phone_normalization(self):
        """Teste la normalisation automatique du numéro."""
        payload = PaymentPayload(
            amount=5000,
            clientPhoneNumber="243972345678",
            country_target=CountryCode.DRC,
        )
        
        # Le SDK devrait ajouter le +
        assert payload.clientPhoneNumber == "+243972345678"
    
    def test_invalid_phone_format(self):
        """Teste qu'un numéro invalide lève une exception Pydantic."""
        with pytest.raises(PydanticValidationError):
            PaymentPayload(
                amount=5000,
                clientPhoneNumber="not-a-phone",
                country_target=CountryCode.DRC,
            )
    
    def test_country_phone_mismatch_drc(self):
        """Teste qu'on ne peut pas envoyer Kenya vers DRC."""
        with pytest.raises(PydanticValidationError):
            PaymentPayload(
                amount=5000,
                clientPhoneNumber="+254700000000",  # Kenya
                country_target=CountryCode.DRC,
            )
    
    def test_minimum_amount_drc(self):
        """Teste que le montant minimum RDC (2900) est enforçé."""
        with pytest.raises(PydanticValidationError):
            PaymentPayload(
                amount=100,
                clientPhoneNumber="+243972345678",
                country_target=CountryCode.DRC,
            )
    
    def test_minimum_amount_drc_exact(self):
        """Teste que le montant exact minimum RDC (2900) est accepté."""
        payload = PaymentPayload(
            amount=2900,
            clientPhoneNumber="+243972345678",
            country_target=CountryCode.DRC,
        )
        
        assert payload.amount == 2900
    
    def test_optional_callback_url(self):
        """Teste que callbackUrl est optionnel."""
        payload = PaymentPayload(
            amount=5000,
            clientPhoneNumber="+243972345678",
            country_target=CountryCode.DRC,
            # callbackUrl omis
        )
        
        assert payload.callbackUrl is None
    
    def test_negative_amount_rejected(self):
        """Teste que les montants négatifs sont rejetés."""
        with pytest.raises(PydanticValidationError):
            PaymentPayload(
                amount=-5000,
                clientPhoneNumber="+243972345678",
                country_target=CountryCode.DRC,
            )
    
    def test_zero_amount_rejected(self):
        """Teste que les montants zéro sont rejetés."""
        with pytest.raises(PydanticValidationError):
            PaymentPayload(
                amount=0,
                clientPhoneNumber="+243972345678",
                country_target=CountryCode.DRC,
            )


class TestPaymentResponse:
    """Tests du modèle PaymentResponse."""
    
    def test_valid_response(self):
        """Teste la création d'une réponse valide."""
        response = PaymentResponse(
            id="trans-123",
            status="pending",
            isSandbox=True,
        )
        
        assert response.id == "trans-123"
        assert response.status == "pending"
        assert response.isSandbox is True
    
    def test_response_with_extra_fields(self):
        """Teste que des champs additionnels sont acceptés."""
        response = PaymentResponse(
            id="trans-123",
            status="pending",
            isSandbox=True,
            extra_field="extra_value",
        )
        
        assert response.id == "trans-123"
        assert response.extra_field == "extra_value"


class TestTransactionResponse:
    """Tests du modèle TransactionResponse."""
    
    def test_valid_response(self):
        """Teste la création d'une réponse transaction valide."""
        response = TransactionResponse(
            id="trans-456",
            status="completed",
            amount=5000,
            recipientPhoneNumber="+243972345678",
        )
        
        assert response.id == "trans-456"
        assert response.status == "completed"
        assert response.amount == 5000
    
    def test_optional_fields(self):
        """Teste que les champs optionnels peuvent être omis."""
        response = TransactionResponse(
            id="trans-456",
            status="pending",
            amount=1000,
            # Les champs suivants sont optionnels:
            # recipientPhoneNumber, createdAt, updatedAt, metadata
        )
        
        assert response.recipientPhoneNumber is None


class TestWebhookPayload:
    """Tests du modèle WebhookPayload."""
    
    def test_valid_webhook_payload(self):
        """Teste la création d'une charge webhook valide."""
        payload = WebhookPayload(
            id="trans-webhook",
            status="completed",
            amount=5000,
        )
        
        assert payload.id == "trans-webhook"
        assert payload.status == "completed"
        assert payload.amount == 5000
    
    def test_webhook_with_metadata(self):
        """Teste qu'on peut inclure des métadonnées."""
        now = datetime.now()
        payload = WebhookPayload(
            id="trans-webhook",
            status="completed",
            amount=5000,
            metadata={"updated_at": now},
        )

        assert payload.metadata["updated_at"] == now
    
    def test_webhook_required_fields(self):
        """Teste que les champs requis sont obligatoires."""
        with pytest.raises(PydanticValidationError):
            WebhookPayload(
                id="trans-webhook",
                # status manquant
                amount=5000,
            )