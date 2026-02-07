"""
Logique métier partagée entre les clients Sync et Async.

Ce module contient notamment les fonctions de validation et de préparation des requêtes
utilisées par tous les clients Shwary pour éviter la duplication de code.

Fonctions principales:
- prepare_payment_request: Valide et prépare les données de paiement

Exemple d'utilisation directe:
    from shwary.core import prepare_payment_request
    
    endpoint, payload = prepare_payment_request(
        country="DRC",
        amount=5000,
        phone="+243972345678",
        is_sandbox=True
    )
    # endpoint = "/payment/sandbox/DRC"
    # payload = {"amount": 5000, "clientPhoneNumber": "+243972345678"}
"""

from typing import Any

import httpx
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import ValidationError
from .schemas import CountryCode, PaymentPayload


def prepare_payment_request(
    country: str | CountryCode,
    amount: float,
    phone: str,
    callback: str | None = None,
    is_sandbox: bool = False,
) -> tuple[str, dict]:
    """
    Prépare les données d'une requête de paiement pour envoi à Shwary.
    
    Cette fonction centralise toute la logique de validation et de préparation,
    partagée entre les clients sync et async pour éviter la duplication.
    
    **Validations effectuées:**
    
    1. **Phone (Numéro de téléphone)**
       - Accepte formats: +243972345678, 243972345678, 0972345678
       - Normalise en E.164: +243972345678
       - Valide que le numéro existe vraiment
    
    2. **Country (Pays)**
       - Accepte DRC, KE, UG (case insensitive)
       - Chèque cohérence country/prefix téléphone
         - DRC: +243
         - KE: +254
         - UG: +256
    
    3. **Amount (Montant)**
       - Doit être > 0
       - RDC: minimum 2900 CDF
       - Kenya/Ouganda: > 0 (pas de minimum strict)
    
    4. **Callback (URL de webhook)**
       - Optionnel
       - Peut être None
    
    Args:
        country: Code du pays (str ou enum CountryCode)
                 Accepte: "DRC", "KE", "UG" (case-insensitive)
        amount: Montant de la transaction (doit être > 0)
                Sera typé en float. Montant en devise locale du pays.
        phone: Numéro de téléphone du client
               Accepte plusieurs formats:
               - "+243972345678" (international)
               - "243972345678" (sans +)
               - "0972345678" (numéro local)
        callback: URL de callback optionnelle pour les notifications webhook
                 Si None, Shwary n'enverra pas de webhook
        is_sandbox: Si True, utilise l'endpoint sandbox pour test
                   Si False, accède directement à la production
        
    Returns:
        Tuple[str, dict]: Contient l'endpoint et le payload validés
        
        - endpoint (str): URL relative à utiliser
          Exemples: "/payment/sandbox/DRC", "/payment/KE"
        
        - payload (dict): Dictionnaire avec champs validés
          ```python
          {
              "amount": 5000.0,
              "clientPhoneNumber": "+243972345678",
              "callbackUrl": "https://example.com/webhook"  # optionnel
          }
          ```
        
    Raises:
        ValidationError: Si l'une des validations échoue
        
            Cas d'erreur possibles:
            - Numéro invalide: "Format de numéro impossible à analyser"
            - Pays invalide: "Pays non supporté"
            - Montant invalide: "Le montant doit être > 0"
            - RDC montant bas: "Le montant minimum pour la RDC est de 2900 CDF"
            - Cohérence pays/phone: "Le numéro +254... ne correspond pas à DRC"
        
    Example:
        Initialisation basique (production):
        
        >>> from shwary.core import prepare_payment_request
        >>> endpoint, payload = prepare_payment_request(
        ...     country="DRC",
        ...     amount=5000,
        ...     phone="+243972345678",
        ...     is_sandbox=False
        ... )
        >>> print(f"Endpoint: {endpoint}")
        Endpoint: /payment/DRC
        >>> print(payload)
        {'amount': 5000, 'clientPhoneNumber': '+243972345678'}
        
        Avec callback (test):
        
        >>> endpoint, payload = prepare_payment_request(
        ...     country="KE",
        ...     amount=150.50,
        ...     phone="+254700000000",
        ...     callback="https://myapp.com/webhook/shwary",
        ...     is_sandbox=True
        ... )
        >>> print(f"Endpoint: {endpoint}")
        Endpoint: /payment/sandbox/KE
        >>> print(payload)
        {'amount': 150.5, 'clientPhoneNumber': '+254700000000', 'callbackUrl': '...'}
        
        Numéro qui sera normalisé:
        
        >>> endpoint, payload = prepare_payment_request(
        ...     country="UG",
        ...     amount=1000,
        ...     phone="256700000000",  # Sans le +
        ...     is_sandbox=True
        ... )
        >>> print(payload["clientPhoneNumber"])
        +256700000000
        
    Note:
        Cette fonction est appelée automatiquement par les clients Shwary/ShwaryAsync.
        Vous ne devrez l'appeler directement que si vous implémentez un client custom.
    """
    try:
        # Convertit string vers enum CountryCode si nécessaire
        country_enum: CountryCode = (
            CountryCode(country) if isinstance(country, str) else country
        )
        
        # Validation Pydantic : effectue tous les checks et normalise
        payload: PaymentPayload = PaymentPayload(
            amount=amount,
            clientPhoneNumber=phone,
            callbackUrl=callback,
            country_target=country_enum
        )
    except ValueError as e:
        # Capture les erreurs Pydantic et les relance en ValidationError du SDK
        raise ValidationError(str(e)) from e

    # Construction de l'endpoint
    env_path: str = "sandbox/" if is_sandbox else ""
    endpoint: str = f"/payment/{env_path}{country_enum.value}"

    return endpoint, payload.model_dump(exclude={'country_target'}, exclude_none=True)


def get_retrying_options() -> dict[str, Any]:
    return {
            "retry": retry_if_exception_type(
                (httpx.TimeoutException, httpx.ConnectError)
            ),
            "stop": stop_after_attempt(3),
            "wait": wait_exponential(multiplier=1, min=2, max=10),
            "reraise": True,
        }