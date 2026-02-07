"""
Exemple d'intégration Flask avec Shwary SDK.

Démontre :
- Initialiser un paiement via endpoint POST
- Recevoir et traiter les webhooks Shwary
- Récupérer le statut d'une transaction
- Gestion complète des erreurs
"""

import logging
import os

from flask import Flask, jsonify, request

from shwary import (
    AuthenticationError,
    InsufficientFundsError,
    RateLimitingError,
    Shwary,
    ShwaryAPIError,
    ValidationError,
    configure_logging,
)

# Configure le logging du SDK
configure_logging(log_level=logging.INFO)

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Crée un client Shwary synchrone (idéal pour Flask)
# En production, utilisez les variables d'environnement
shwary_client = Shwary(
    merchant_id=os.environ.get("SHWARY_MERCHANT_ID", "your-merchant-id"),
    merchant_key=os.environ.get("SHWARY_MERCHANT_KEY", "your-merchant-key"),
    is_sandbox=True,  # False en production
    timeout=30.0
)


@app.teardown_appcontext
def shutdown_shwary(exception=None):
    """Ferme le client Shwary à l'arrêt de l'app."""
    try:
        shwary_client.close()
        logger.info("Shwary client closed")
    except Exception as e:
        logger.error(f"Error closing Shwary client: {e}")


@app.route("/api/payments/initiate", methods=["POST"])
def initiate_payment():
    """
    Initialise un paiement Shwary.
    
    **Body JSON:**
    ```json
    {
        "phone": "+243972345678",
        "amount": 5000,
        "country": "DRC",
        "callback_url": "https://example.com/webhook"  // optionnel
    }
    ```
    
    **Réponses:**
    - 200: Transaction initiée avec succès
    - 400: Erreur de validation
    - 401: Identifiants invalides
    - 402: Solde insuffisant
    - 429: Rate limited
    - 500: Erreur serveur
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
    
    phone = data.get("phone")
    amount = data.get("amount")
    country = data.get("country")
    callback_url = data.get("callback_url")
    
    # Validation minimale
    if not phone or amount is None or country is None:
        return jsonify({"error": "Missing required fields: phone, amount, country"}), 400
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "amount must be a number"}), 400
    
    logger.info(f"Payment initiation: {phone} ({country}) - {amount}")
    
    try:
        payment = shwary_client.initiate_payment(
            country=country,
            amount=amount,
            phone_number=phone,
            callback_url=callback_url
        )
        
        logger.info(f"Payment initiated: {payment['id']}")
        
        return jsonify({
            "success": True,
            "transaction_id": payment["id"],
            "status": payment["status"],
            "is_sandbox": payment.get("isSandbox")
        }), 200
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        return jsonify({
            "error": "validation_error",
            "message": str(e)
        }), 400
    
    except AuthenticationError as e:
        logger.error(f"Auth error: {e}")
        return jsonify({
            "error": "authentication_error",
            "message": "Shwary merchant credentials invalid"
        }), 401
    
    except InsufficientFundsError as e:
        logger.warning(f"Insufficient funds: {e}")
        return jsonify({
            "error": "insufficient_balance",
            "message": "Merchant account balance is insufficient"
        }), 402
    
    except RateLimitingError as e:
        logger.warning(f"Rate limited: {e}")
        return jsonify({
            "error": "rate_limited",
            "message": "Too many requests - please retry after a moment"
        }), 429
    
    except ShwaryAPIError as e:
        logger.error(f"API error {e.status_code}: {e.message}")
        return jsonify({
            "error": "shwary_error",
            "message": e.message,
            "status_code": e.status_code
        }), min(e.status_code, 502)
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return jsonify({
            "error": "internal_error",
            "message": "Internal server error"
        }), 500


@app.route("/api/webhooks/shwary", methods=["POST"])
def handle_shwary_webhook():
    """
    Reçoit les notifications de changement d'état de transactions.
    
    Shwary envoie une notification lorsqu'une transaction change d'état.
    
    **Payload attendu:**
    ```json
    {
        "id": "transaction-uuid",
        "status": "completed|failed|pending",
        "amount": 5000,
        "timestamp": "2026-02-06T10:30:00Z"
    }
    ```
    """
    data = request.get_json()
    
    if not data:
        logger.warning("Webhook received with no JSON body")
        return jsonify({"status": "error", "message": "No JSON body"}), 400
    
    transaction_id = data.get("id")
    status = data.get("status")
    amount = data.get("amount")
    
    logger.info(f"Webhook: {transaction_id} -> {status} ({amount})")
    
    try:
        if status == "completed":
            # Transaction réussie
            logger.info(f"Payment completed: {transaction_id}")
            # TODO: deliver_service(transaction_id)
            # TODO: update_database(transaction_id, status="completed")
        
        elif status == "failed":
            # Transaction échouée
            logger.warning(f"Payment failed: {transaction_id}")
            # TODO: notify_customer(transaction_id, "payment_failed")
            # TODO: update_database(transaction_id, status="failed")
        
        elif status == "pending":
            # En attente
            logger.info(f"Payment pending: {transaction_id}")
        
        return jsonify({
            "status": "ok",
            "transaction_id": transaction_id
        }), 200
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Important: retourner 200 même si erreur
        # (Shwary ne retente que sur 5xx)
        return jsonify({
            "status": "ok",
            "message": "Webhook received but processing failed (retry later)"
        }), 200


@app.route("/api/transactions/<transaction_id>", methods=["GET"])
def get_transaction_status(transaction_id):
    """
    Récupère le statut actualisé d'une transaction.
    
    Utile pour :
    - Polling si webhook non reçu
    - Vérification de statut à la demande
    """
    logger.info(f"Fetching transaction: {transaction_id}")
    
    try:
        tx = shwary_client.get_transaction(transaction_id)
        
        logger.info(f"Transaction: {transaction_id} - {tx.get('status')}")
        
        return jsonify({
            "id": tx["id"],
            "status": tx["status"],
            "amount": tx.get("amount"),
            "phone": tx.get("clientPhoneNumber"),
            "created_at": tx.get("createdAt"),
            "updated_at": tx.get("updatedAt")
        }), 200
    
    except ShwaryAPIError as e:
        if e.status_code == 404:
            logger.warning(f"Transaction not found: {transaction_id}")
            return jsonify({"error": "not_found"}), 404
        
        logger.error(f"Error fetching transaction: {e}")
        return jsonify({
            "error": "api_error",
            "message": e.message
        }), min(e.status_code, 502)


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint pour les load balancers."""
    return jsonify({
        "status": "healthy",
        "service": "shwary-payment-api"
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handler pour 404."""
    return jsonify({"error": "not_found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler pour erreurs 500."""
    logger.exception(f"Internal error: {error}")
    return jsonify({"error": "internal_error"}), 500


if __name__ == "__main__":
    # Configuration
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.environ.get("PORT", 5000))
    
    # Lance le serveur
    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode
    )
