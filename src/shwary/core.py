from typing import Any
from .schemas import PaymentPayload, CountryCode
from .exceptions import ValidationError

def prepare_payment_request(
    country: CountryCode | str,
    amount: float, 
    phone: str, 
    callback: str, 
    is_sandbox: bool
) -> tuple[str, dict[str, Any]]:
    """
    Prépare l'URL et le Payload validé.
    Partagé par les clients Sync et Async pour éviter la duplication de logique métier.
    """
    # Validation & Conversion
    try:
        country_enum: CountryCode = CountryCode(country) if isinstance(country, str) else country
        payload: PaymentPayload = PaymentPayload(
            amount=amount,
            clientPhoneNumber=phone,
            callbackUrl=callback,
            country_target=country_enum
        )
    except ValueError as e:
        # On capture les erreurs Pydantic pour les relancer en ValidationError du SDK
        raise ValidationError(str(e)) from e

    env_path: str = "sandbox/" if is_sandbox else ""
    endpoint: str = f"/payment/{env_path}{country_enum.value}"

    return endpoint, payload.model_dump(exclude={'country_target'}, exclude_none=True)
