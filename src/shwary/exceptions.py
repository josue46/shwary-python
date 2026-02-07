"""
Exceptions personnalisées du SDK Shwary.

Permet une gestion d'erreurs granulaire sans vérifier les status_code manuellement.
"""

from http import HTTPStatus
from typing import Any, Optional

from httpx import Response


class ShwaryError(Exception):
    """
    Exception de base pour toutes les erreurs Shwary.
    
    Héritez de cette classe pour créer des exceptions personnalisées.
    """
    pass


class ValidationError(ShwaryError):
    """
    Levée avant même l'envoi de la requête (validation locale).
    
    Cas d'usage:
    - Numéro de téléphone invalide
    - Montant négatif ou zéro
    - Cohérence pays/numéro manquante
    - Format de pays invalide
    """
    pass


class AuthenticationError(ShwaryError):
    """
    Levée sur une erreur 401 (Unauthorized).
    
    Cas d'usage:
    - Clé API invalide
    - Identifiant marchand incorrect
    - Credentials expirées
    """
    pass


class InsufficientFundsError(ShwaryError):
    """
    Levée si le solde marchand est insuffisant ou règles métiers non respectées.
    
    Cas d'usage:
    - Solde marchand < montant demandé
    - Limite de transactions dépassée
    - VAS (Value Added Services) non activé
    """
    pass


class RateLimitingError(ShwaryError):
    """Levée sur une erreur 429 (Too Many Requests)."""
    pass


class ShwaryAPIError(ShwaryError):
    """
    Erreur générique retournée par l'API Shwary (4xx, 5xx sauf cas spécialisés).
    
    Attributes:
        status_code: Code HTTP de la réponse
        message: Message d'erreur retourné par l'API
        raw_response: Réponse brute JSON de l'API pour debugging
    """
    
    def __init__(
        self,
        status_code: int,
        message: str,
        raw_response: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialise une exception ShwaryAPIError.
        
        Args:
            status_code: Code HTTP de la réponse
            message: Message d'erreur
            raw_response: Réponse JSON brute (optionnelle)
        """
        self.status_code = status_code
        self.raw_response = raw_response or {}
        self.message = message
        
        # Tente de résoudre le status HTTP pour un message plus lisible
        try:
            http_status = HTTPStatus(status_code)
            status_name = http_status.name
        except ValueError:
            status_name = "UNKNOWN"
        
        super().__init__(
            f"Shwary API Error {status_code} ({status_name}): {message}"
        )


def raise_from_response(response: Response) -> None:
    """
    Convertit une réponse HTTP en exception Python si elle indique une erreur.
    
    Cette fonction centralise la logique de conversion des erreurs HTTP.
    Ne lève rien si la requête a réussi (2xx).
    
    Args:
        response: Réponse httpx (sync ou async)
        
    Raises:
        ValidationError: Pour erreur 400
        AuthenticationError: Pour erreur 401
        RateLimitingError: Pour erreur 429
        InsufficientFundsError: Pour erreur 400 avec "balance"
        ShwaryAPIError: Pour tous les autres codes d'erreur
    """
    if response.is_success:
        return

    status = response.status_code
    
    # Essaye de parser le JSON de la réponse
    data: dict[str, Any] = {}
    try:
        data = response.json()
        message = data.get("message", response.text)
    except Exception:
        message = response.text
    
    # Dispatch vers l'exception appropriée selon le status code
    if status == 400 and "balance" in message.lower():
        raise InsufficientFundsError(f"Solde insuffisant : {message}")

    match(status):
        case 401:
            raise AuthenticationError(f"Échec d'authentification : {message}")
        case 429:
            raise RateLimitingError(f"Trop de requêtes (Rate limited) : {message}")
        case _:
            raise ShwaryAPIError(status, message, raw_response=data)

