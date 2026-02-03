class ShwaryError(Exception):
    """Exception de base pour toutes les erreurs Shwary."""
    pass

class ValidationError(ShwaryError):
    """Levée avant même l'envoi de la requête (ex: mauvais numéro)."""
    pass

class AuthenticationError(ShwaryError):
    """Levée sur une erreur 401 (Clé API invalide)."""
    pass

class InsufficientFundsError(ShwaryError):
    """Levée si le solde marchand est insuffisant ou règles métiers non respectées."""
    pass

class ShwaryAPIError(ShwaryError):
    """Erreur générique retournée par l'API (400, 500, etc.)."""
    def __init__(self, status_code: int, message: str, raw_response: dict = None):
        self.status_code = status_code
        self.raw_response = raw_response
        super().__init__(f"Shwary Error {status_code}: {message}")

def raise_from_response(response):
    """Helper pour convertir une réponse HTTP en exception Python."""
    if response.is_success:
        return

    status = response.status_code
    try:
        data = response.json()
        message = data.get("message", response.text)
    except Exception:
        message = response.text

    if status == 401:
        raise AuthenticationError(f"Échec d'authentification : {message}")
    elif status == 400 and "balance" in message.lower():
        raise InsufficientFundsError(message)
    else:
        raise ShwaryAPIError(status, message, raw_response=data if 'data' in locals() else None)