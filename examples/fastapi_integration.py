"""
Exemple d'intégration FastAPI avec Shwary SDK.

Démontre :
- Initialiser un paiement via endpoint POST
- Recevoir et traiter les webhooks Shwary
- Récupérer le statut d'une transaction
- Gestion complète des erreurs
"""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from shwary import (
    AuthenticationError,
    InsufficientFundsError,
    RateLimitingError,
    ShwaryAPIError,
    ShwaryAsync,
    ValidationError,
    WebhookPayload,
    configure_logging,
)

# Configure le logging du SDK
configure_logging(log_level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shwary Payment API",
    description="API de paiement intégrée avec Shwary",
    version="1.0.0",
)

# Crée une instance du client (réutilisée pour chaque requête)
# En production, utilisez les variables d'environnement ou un secret manager
shwary_client = ShwaryAsync(
    merchant_id="your-merchant-id-uuid",
    merchant_key="your-merchant-secret-key",
    is_sandbox=True,  # False en production
    timeout=30.0,
)


@app.on_event("startup")
async def startup():
    """Événement de démarrage de l'app."""
    logger.info("FastAPI startup - Shwary client initialized")


@app.on_event("shutdown")
async def shutdown():
    """Ferme proprement le client Shwary à l'arrêt."""
    await shwary_client.close()
    logger.info("FastAPI shutdown - Shwary client closed")


@app.post("/api/payments/initiate")
async def initiate_payment(
    phone: str, amount: float, country: str = "DRC", callback_url: str | None = None
):
    """
    Initialise un paiement Shwary.

    **Paramètres:**
    - phone: Numéro au format E.164 (ex: +243972345678)
    - amount: Montant de la transaction
    - country: Code du pays (DRC, KE, UG) - défaut: DRC
    - callback_url: URL de callback optionnelle pour les notifications

    **Réponses:**
    - 200: Transaction initiée avec succès
    - 400: Erreur de validation (numéro, montant, etc.)
    - 401: Identifiants Shwary invalides
    - 402: Solde marchand insuffisant
    - 429: Trop de requêtes - retry plus tard
    - 500: Erreur serveur
    """
    logger.info(f"Payment initiation requested: {phone} ({country}) - {amount}")

    try:
        # Utilise le client asynchrone pour ne pas bloquer
        async with shwary_client as client:
            payment = await client.initiate_payment(
                country=country,
                amount=amount,
                phone_number=phone,
                callback_url=callback_url,
            )

        logger.info(f"Payment initiated successfully: {payment.id}")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "transaction_id": payment.id,
                "status": payment.status,
                "is_sandbox": payment.is_sandbox,
            },
        )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Shwary authentication failed - check merchant credentials",
        )

    except InsufficientFundsError as e:
        logger.warning(f"Insufficient funds: {e}")
        raise HTTPException(
            status_code=402, detail="Merchant account has insufficient balance"
        )

    except RateLimitingError as e:
        logger.warning(f"Rate limited: {e}")
        raise HTTPException(
            status_code=429, detail="Too many requests - retry after some time"
        )

    except ShwaryAPIError as e:
        logger.error(f"Shwary API error {e.status_code}: {e.message}")
        raise HTTPException(
            status_code=min(e.status_code, 502),  # Map 5xx to 502
            detail=f"Shwary API error: {e.message}",
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/webhooks/shwary")
async def handle_shwary_webhook(payload: WebhookPayload):
    """
    Reçoit les notifications de changement d'état de transactions.

    Shwary envoie une notification JSON lorsqu'une transaction change d'état.

    **Payload attendu:**
    ```json
    {
        "id": "transaction-uuid",
        "status": "completed|failed|pending",
        "amount": 5000,
        "timestamp": "2025-02-06T10:30:00Z",
        "metadata": {}
    }
    ```
    """
    logger.info(f"Webhook received: {payload.id} -> {payload.status}")

    try:
        if payload.status == "completed":
            # Transaction réussie - livrez le service
            logger.info(f"Payment completed: {payload.id}")
            # await deliver_service(payload.id)
            # await update_database(payload.id, "completed")

        elif payload.status == "failed":
            # Transaction échouée
            logger.warning(f"Payment failed: {payload.id}")
            # await notify_user_payment_failed(payload.id)
            # await update_database(payload.id, "failed")

        elif payload.status == "pending":
            # En attente (rare pour les webhooks)
            logger.info(f"Payment pending: {payload.id}")

        return JSONResponse(
            status_code=200, content={"status": "ok", "transaction_id": payload.id}
        )

    except Exception as e:
        logger.exception(f"Error handling webhook: {e}")
        # Important: retourner 200 même si erreur (Shwary ne rejette que les 5xx)
        return JSONResponse(
            status_code=200, content={"status": "error", "message": str(e)}
        )


@app.get("/api/transactions/{transaction_id}")
async def get_transaction_status(transaction_id: str):
    """
    Récupère le statut actualisé d'une transaction.

    Utile si vous n'avez pas reçu le webhook ou pour un polling.
    """
    logger.info(f"Fetching transaction: {transaction_id}")

    try:
        async with shwary_client as client:
            tx = await client.get_transaction(transaction_id)

        logger.info(f"Transaction fetched: {transaction_id} - {tx.get('status')}")

        return JSONResponse(
            status_code=200,
            content={
                "id": tx["id"],
                "status": tx["status"],
                "amount": tx.get("amount"),
                "phone": tx.get("clientPhoneNumber"),
                "created_at": tx.get("createdAt"),
                "updated_at": tx.get("updatedAt"),
            },
        )

    except ShwaryAPIError as e:
        if e.status_code == 404:
            logger.warning(f"Transaction not found: {transaction_id}")
            raise HTTPException(status_code=404, detail="Transaction not found")

        logger.error(f"Error fetching transaction: {e}")
        raise HTTPException(
            status_code=min(e.status_code, 502),
            detail="Failed to fetch transaction status",
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200, content={"status": "healthy", "service": "shwary-payment-api"}
    )


if __name__ == "__main__":
    import uvicorn

    # Lance le serveur
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
