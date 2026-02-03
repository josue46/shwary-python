import httpx
from ..core import prepare_payment_request
from ..exceptions import raise_from_response


class Shwary:
    """
    Client synchrone pour l'API Shwary.
    À utiliser pour des scripts `standard, Django, Flask,` etc.
    Doit être utilisé comme context manager ou fermé manuellement.
    """
    __slots__ = ('merchant_id', 'merchant_key', 'is_sandbox', '_client', '_base_url')

    def __init__(self, merchant_id: str, merchant_key: str, is_sandbox: bool = False, timeout: float = 30.0):
        self.is_sandbox = is_sandbox
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key
        self._base_url = "https://api.shwary.com/api/v1/merchants"
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "x-merchant-id": merchant_id,
                "x-merchant-key": merchant_key,
                "Content-Type": "application/json",
                "User-Agent": "Shwary-Python-SDK/0.1.0"
            }
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def initiate_payment(self, country: str, amount: float, phone_number: str, callback_url: str = None) -> dict:
        """Initie une demande de paiement."""

        endpoint, json_data = prepare_payment_request(country, amount, phone_number, callback_url, self.is_sandbox)
        
        response = self._client.post(endpoint, json=json_data)
        
        raise_from_response(response)
        
        return response.json()
    
    def get_transaction(self, transaction_id: str) -> dict:
        """
        Récupère les détails d'une transaction unique à partir de son ID.
        """
        endpoint: str = f"/transactions/{transaction_id}"
        response = self._client.get(endpoint)
        
        raise_from_response(response)
        
        return response.json()