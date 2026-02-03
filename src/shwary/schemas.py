from enum import Enum
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BaseModel, Field, field_validator, model_validator

class CountryCode(str, Enum):
    DRC = "DRC"
    KENYA = "KE"
    UGANDA = "UG"

class PaymentPayload(BaseModel):
    amount: float = Field(..., gt=0, description="Montant de la transaction")
    clientPhoneNumber: str = Field(..., description="Numéro au format international")
    callbackUrl: Optional[str] = None
    country_target: CountryCode = Field(..., exclude=True)

    @field_validator("clientPhoneNumber")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            # LazyParsing pour accepter +243... ou 243...
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Numéro de téléphone invalide.")
            
            # Formatage strict E.164 (ex: +24381...) requis par Shwary
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            raise ValueError("Format de numéro impossible à analyser.")

    @model_validator(mode='after')
    def validate_country_consistency(self):
        """
        Fait une validation croisée :
        On ne peut pas envoyer un numéro +254 (Kenya) vers l'endpoint DRC
        """

        phone: str = self.clientPhoneNumber
        country: CountryCode = self.country_target
        
        prefixes: dict[CountryCode, str] = {
            CountryCode.DRC: "+243",
            CountryCode.KENYA: "+254",
            CountryCode.UGANDA: "+256"
        }
        
        expected_prefix = prefixes.get(country)
        if expected_prefix and not phone.startswith(expected_prefix):
             raise ValueError(f"Le numéro {phone} ne correspond pas au pays ciblé ({country.value}).")
        
        # Règle métier Shwary : Montant min pour RDC
        if country == CountryCode.DRC and self.amount < 2900:
             raise ValueError("Le montant minimum pour la RDC est de 2900 CDF.")
             
        return self