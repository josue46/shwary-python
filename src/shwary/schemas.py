from datetime import datetime
from enum import Enum
from typing import Any, Optional

import phonenumbers
from phonenumbers import NumberParseException
from pydantic import BaseModel, Field, model_validator


class CountryCode(str, Enum):
    """Codes des pays supportés par Shwary."""

    DRC = "DRC"
    KENYA = "KE"
    UGANDA = "UG"


class PaymentPayload(BaseModel):
    """
    Modèle de validation pour une demande de paiement.

    Effectue des validations métier strictes :
    - Numéro de téléphone au format E.164
    - Cohérence pays/préfixe téléphone
    - Montant minimum par pays
    """

    amount: float = Field(
        ..., gt=0, description="Montant de la transaction (doit être > 0)"
    )
    clientPhoneNumber: str = Field(
        ..., description="Numéro au format international (E.164)"
    )
    callbackUrl: Optional[str] = Field(
        None, description="URL de callback pour les notifications"
    )
    country_target: CountryCode = Field(
        ..., exclude=True, description="Pays cible (internal)"
    )

    @model_validator(mode="before")
    @classmethod
    def pre_process_phone(cls, data: Any) -> Any:
        """
        Pré-traitement pour ajouter le '+' si l'utilisateur l'a oublié
        mais a mis le code pays (ex: 243...)
        """
        if isinstance(data, dict) and "clientPhoneNumber" in data:
            phone = str(data["clientPhoneNumber"]).strip()

            if phone.startswith(("243", "254", "256")):
                data["clientPhoneNumber"] = f"+{phone}"
        return data

    @model_validator(mode="after")
    def validate_payload(self) -> "PaymentPayload":
        """
        Validation complète : téléphone, cohérence pays et montants.
        """
        phone_raw = self.clientPhoneNumber
        country = self.country_target

        # Utilisation du code pays cible comme région par défaut pour les numéros locaux (ex: 097...)  # noqa: E501
        region_map = {
            CountryCode.DRC: "CD",
            CountryCode.KENYA: "KE",
            CountryCode.UGANDA: "UG",
        }

        try:
            parsed = phonenumbers.parse(phone_raw, region_map.get(country))
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError(
                    f"Le numéro {phone_raw} n'est pas valide pour {country.value}"
                )

            # Mise à jour du téléphone au format propre E.164
            self.clientPhoneNumber = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        except NumberParseException as e:
            raise ValueError(f"Format de numéro impossible à analyser : {str(e)}")

        # Validation de la cohérence pays/préfixe
        prefixes = {
            CountryCode.DRC: "+243",
            CountryCode.KENYA: "+254",
            CountryCode.UGANDA: "+256",
        }

        expected_prefix = prefixes.get(country)
        if expected_prefix and not self.clientPhoneNumber.startswith(expected_prefix):
            raise ValueError(
                f"Le numéro {self.clientPhoneNumber} ne correspond pas à {country.value}."  # noqa: E501
            )

        # Validation des montants minimums
        min_amounts = {
            CountryCode.DRC: 2900.0,
            CountryCode.KENYA: 1.0,
            CountryCode.UGANDA: 1.0,
        }

        min_amount = min_amounts.get(country, 1.0)
        if self.amount < min_amount:
            raise ValueError(
                f"Montant minimum pour {country.value} : {min_amount}. Reçu : {self.amount}"  # noqa: E501
            )

        return self


class PaymentResponse(BaseModel):
    """
    Réponse d'une demande de paiement initiée avec succès.

    Attributes:
        id: Identifiant unique de la transaction (UUID)
        status: État de la transaction (pending, completed, failed, etc.)
        isSandbox: True si la transaction est en mode sandbox
    """

    id: str = Field(..., description="Identifiant unique de la transaction (UUID)")
    status: str = Field(..., description="État de la transaction")
    isSandbox: bool = Field(
        ..., description="Indique si la transaction est en mode sandbox"
    )

    model_config = {"extra": "allow"}


class TransactionResponse(BaseModel):
    """
    Réponse détaillée d'une transaction à partir de son ID.

    Attributes:
        id: Identifiant unique de la transaction
        status: État actualisé de la transaction
        amount: Montant de la transaction
        recipientPhoneNumber: Numéro du receveur
        createdAt: Timestamp de création
        updatedAt: Timestamp de dernière mise à jour
        metadata: Données métier additionnelles
    """

    id: str = Field(..., description="Identifiant unique de la transaction")
    status: str = Field(
        ..., description="État actualisé (pending, completed, failed, etc.)"
    )
    amount: float = Field(..., description="Montant de la transaction")
    recipientPhoneNumber: Optional[str] = Field(None, description="Numéro du receveur")
    createdAt: Optional[datetime] = Field(None, description="Timestamp de création")
    updatedAt: Optional[datetime] = Field(
        None, description="Timestamp de dernière mise à jour"
    )
    metadata: Optional[dict] = Field(None, description="Données métier additionnelles")

    model_config = {"extra": "allow"}


class WebhookPayload(BaseModel):
    """
    Charge utile reçue via webhook lorsqu'une transaction change d'état.

    À utiliser pour traiter les notifications Shwary.

    Attributes:
        id: Identifiant de la transaction
        status: Nouveau statut (pending, completed, failed)
        amount: Montant de la transaction
        timestamp: Quand le changement s'est produit
        metadata: Données additionnelles de Shwary

    Example:
        from fastapi import FastAPI, Request
        from shwary.schemas import WebhookPayload

        app = FastAPI()

        @app.post("/webhooks/shwary")
        async def handle_shwary_webhook(payload: WebhookPayload):
            if payload.status == "completed":
                # Transaction réussie
                print(f"Transaction {payload.id} complétée!")
            return {"status": "ok"}
    """

    id: str = Field(..., description="ID de la transaction")
    status: str = Field(..., description="Nouveau statut")
    amount: float = Field(..., description="Montant de la transaction")
    metadata: Optional[dict] = Field(None, description="Données Shwary additionnelles")

    model_config = {"extra": "allow"}
