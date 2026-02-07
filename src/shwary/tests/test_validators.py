"""Tests des validateurs Shwary."""

from shwary.schemas import CountryCode
from shwary.validators import (
    validate_amount,
    validate_callback_url,
    validate_merchant_id,
    validate_transaction_id,
)


class TestCallbackUrlValidation:
    """Tests de validation d'URL de callback."""
    
    def test_valid_https_callback(self):
        """Teste une URL HTTPS valide."""
        assert validate_callback_url("https://example.com/webhook") is True
    
    def test_valid_http_callback(self):
        """Teste une URL HTTP valide."""
        assert validate_callback_url("http://example.com/webhook") is True
    
    def test_invalid_callback_no_scheme(self):
        """Teste qu'une URL sans scheme est rejetée."""
        assert validate_callback_url("example.com/webhook") is False
    
    def test_invalid_callback_wrong_scheme(self):
        """Teste qu'une URL avec mauvais scheme est rejetée."""
        assert validate_callback_url("ftp://example.com/webhook") is False
    
    def test_none_callback_is_valid(self):
        """Teste que None (callback optionnel) est accepté."""
        assert validate_callback_url(None) is True
    
    def test_empty_callback_is_valid(self):
        """Teste que string vide est acceptée."""
        assert validate_callback_url("") is True


class TestMerchantIdValidation:
    """Tests de validation d'ID marchand."""
    
    def test_valid_uuid4_merchant_id(self):
        """Teste un UUID v4 valide."""
        assert validate_merchant_id("550e8400-e29b-41d4-a716-446655440000") is True
    
    def test_valid_uuid4_lowercase(self):
        """Teste un UUID v4 en minuscules."""
        assert validate_merchant_id("6ba7b810-9dad-11d1-80b4-00c04fd430c8") is True
    
    def test_invalid_merchant_id_no_dashes(self):
        """Teste qu'un UUID sans dashes est rejeté."""
        assert validate_merchant_id("550e8400e29b41d4a716446655440000") is False
    
    def test_invalid_merchant_id_wrong_format(self):
        """Teste qu'un format non UUID est rejeté."""
        assert validate_merchant_id("not-a-valid-uuid") is False
    
    def test_invalid_merchant_id_extra_chars(self):
        """Teste qu'un UUID avec caractères extra est rejeté."""
        assert validate_merchant_id("550e8400-e29b-41d4-a716-44665544000X") is False


class TestTransactionIdValidation:
    """Tests de validation d'ID transaction."""
    
    def test_valid_uuid4_transaction_id(self):
        """Teste un UUID v4 valide."""
        assert validate_transaction_id("c0fdfe50-24be-4de1-9f66-84608fd45a5f") is True
    
    def test_invalid_transaction_id_too_short(self):
        """Teste qu'un ID trop court est rejeté."""
        assert validate_transaction_id("12345") is False
    
    def test_invalid_transaction_id_wrong_chars(self):
        """Teste qu'un ID avec caractères invalides est rejeté."""
        assert validate_transaction_id("c0fdfe50-24be-4de1-9f66-84608fd45a5Z") is False


class TestAmountValidation:
    """Tests de validation des montants."""
    
    def test_valid_drc_minimum(self):
        """Teste que le minimum RDC (2900) est accepté."""
        is_valid, msg = validate_amount(2900, CountryCode.DRC)
        assert is_valid is True
        assert msg is None
    
    def test_valid_drc_above_minimum(self):
        """Teste qu'un montant au-dessus du minimum RDC est accepté."""
        is_valid, msg = validate_amount(5000, CountryCode.DRC)
        assert is_valid is True
    
    def test_invalid_drc_below_minimum(self):
        """Teste qu'un montant en-dessous du minimum RDC est rejeté."""
        is_valid, msg = validate_amount(1000, CountryCode.DRC)
        assert is_valid is False
        assert "2900" in str(msg)
    
    def test_valid_kenya_minimum(self):
        """Teste que le minimum Kenya (1.0) est accepté."""
        is_valid, msg = validate_amount(1.0, CountryCode.KENYA)
        assert is_valid is True
    
    def test_valid_uganda_minimum(self):
        """Teste que le minimum Ouganda (1.0) est accepté."""
        is_valid, msg = validate_amount(1.0, CountryCode.UGANDA)
        assert is_valid is True
    
    def test_invalid_negative_amount(self):
        """Teste qu'un montant négatif est rejeté."""
        is_valid, msg = validate_amount(-100, CountryCode.DRC)
        assert is_valid is False
        assert "positif" in str(msg).lower()
    
    def test_invalid_zero_amount(self):
        """Teste qu'un montant zéro est rejeté."""
        is_valid, msg = validate_amount(0, CountryCode.DRC)
        assert is_valid is False