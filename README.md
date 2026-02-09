# Shwary Python SDK

[![PyPI version](https://img.shields.io/pypi/v/shwary-python.svg)](https://pypi.org/project/shwary-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/shwary-python.svg)](https://pypi.org/project/shwary-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Shwary Python** est une bibliothèque cliente moderne, asynchrone et performante pour l'intégration de l'API [Shwary](https://shwary.com). Elle permet d'initier des paiements Mobile Money en **RDC**, au **Kenya** et en **Ouganda** avec une validation stricte des données avant l'envoi.

## Quoi de neuf dans la v2.0.2

- **Retry automatique** : Les erreurs réseau transitoires (timeout, connexion) sont automatiquement retentées avec backoff exponentiel
- **Types stricts** : TypedDict pour les réponses (`PaymentResponse`, `TransactionResponse`, `WebhookPayload`)
- **Logging structuré** : Les logs s'écrivent dans la racine du projet utilisateur (`logs/shwary.log`) avec rotation automatique
- **Base class partagée** : Élimination de la duplication sync/async pour une maintenabilité meilleure
- **429 Rate Limiting** : Nouvelle exception `RateLimitingError` pour gérer les dépassements de débit
- **Docstrings améliorées** : Documentation complète avec exemples d'utilisation
- **Tests étendus** : Couverture complète des retries, erreurs et validations
- **Modèles de réponse** : Schemas Pydantic pour les webhooks et transactions
- **Correction des bugs** : Correction des imports et des bugs mineurs

## Caractéristiques

* **Gestion d'erreurs native** : Pas besoin de vérifier les `status_code` manuellement. Le SDK lève des exceptions explicites (`AuthenticationError`, `ValidationError`, etc.).
* **Async-first** : Construit sur `httpx` pour des performances optimales (Pooling de connexions).
* **Dual-mode** : Support complet des modes Synchrone et Asynchrone.
* **Validation Robuste** : Vérification des numéros (E.164) et des montants minimums (ex: 2900 CDF pour la RDC).
* **Retry automatique** : Retries intelligentes sur erreurs réseau transitoires avec backoff exponentiel.
* **Type-safe** : Basé sur Pydantic V2 pour une autocomplétion parfaite dans votre IDE.
* **Ultra-rapide** : Optimisé avec `uv` et `__slots__` pour minimiser l'empreinte mémoire.
* **Logging structuré** : Logs dans la racine du projet utilisateur sans données sensibles.

## Installation

Avec `uv` (recommandé) :
```bash
uv add shwary-python
```
Ou avec `pip`
```bash
pip install shwary-python
```

## Utilisation Rapide

### Mode Synchrone (Flask, Django, scripts)

```python
from shwary import Shwary, ValidationError, AuthenticationError

with Shwary(
    merchant_id="your-merchant-id",
    merchant_key="your-merchant-key",
    is_sandbox=True
) as client:
    try:
        payment = client.initiate_payment(
            country="DRC",
            amount=5000,
            phone_number="+243972345678",
            callback_url="https://yoursite.com/webhooks/shwary"
        )
        print(f"Transaction: {payment['id']} - {payment['status']}")
    except ValidationError as e:
        print(f"Erreur validation: {e}")
    except AuthenticationError:
        print("Credentials invalides")
```

### Mode Asynchrone (FastAPI, Quart, aiohttp)

```python
import asyncio
from shwary import ShwaryAsync

async def main():
    async with ShwaryAsync(
        merchant_id="your-merchant-id",
        merchant_key="your-merchant-key",
        is_sandbox=True
    ) as client:
        try:
            payment = await client.initiate_payment(
                country="DRC",
                amount=5000,
                phone_number="+243972345678"
            )
            print(f"Transaction: {payment['id']}")
        except Exception as e:
            print(f"Erreur: {e}")

asyncio.run(main())
```

## Validation par pays

Le SDK applique les règles métiers de Shwary localement pour économiser des appels réseau :

| Pays | Code | Devise | Montant Min. | Préfixe |
| :--- | :--- | :--- | :--- | :--- |
| RDC | DRC | CDF | 2900 | +243 |
| Kenya | KE | KES | > 0 | +254 |
| Ouganda | UG | UGX | > 0 | +256 |

## Gestion des Erreurs

Le SDK transforme les erreurs HTTP en exceptions Python. **Vous n'avez pas besoin de vérifier manuellement les codes de statut** – gérez simplement les exceptions :

```python
from shwary import (
    Shwary,
    ValidationError,         # Données invalides
    AuthenticationError,      # Credentials invalides
    InsufficientFundsError,  # Solde insuffisant
    RateLimitingError,       # Trop de requêtes
    ShwaryAPIError,          # Erreur serveur
)

try:
    payment = client.initiate_payment(...)
    
except ValidationError as e:
    # Format téléphone invalide, montant trop bas, etc.
    print(f"Erreur validation: {e}")
    
except AuthenticationError:
    # merchant_id / merchant_key incorrects
    print("Credentials invalides - vérifiez votre configuration")
    
except InsufficientFundsError:
    # Solde marchand insuffisant
    print("Solde insuffisant - rechargez votre compte")
    
except RateLimitingError:
    # Trop de requêtes (429) - implémentez un backoff
    print("Rate limited - réessayez dans quelques secondes")
    
except ShwaryAPIError as e:
    # Autres erreurs API (500, timeout, etc.)
    print(f"Erreur API {e.status_code}: {e.message}")
```

## Webhooks et Callbacks

Lorsqu'une transaction change d'état, Shwary envoie une notification JSON à votre `callback_url`. Voici comment la traiter :

```python
from shwary import WebhookPayload

@app.post("/webhooks/shwary")
async def handle_webhook(payload: WebhookPayload):
    """Shwary envoie une notification de changement d'état."""
    
    if payload.status == "completed":
        # Transaction réussie
        print(f"Paiement {payload.id} reçu ({payload.amount})")
        # La livrez le service ici
    
    elif payload.status == "failed":
        # Transaction échouée
        print(f"Paiement {payload.id} échoué")
        # Notifiez le client
    
    return {"status": "ok"}
```

Pour plus d'exemples (FastAPI, Flask), consultez le dossier [examples/](examples/).

## Exemples Complets

Le SDK inclut des exemples d'intégration complets :

### Scripts simples
- [simple_sync.py](examples/simple_sync.py) - Script synchrone basique
- [simple_async.py](examples/simple_async.py) - Script asynchrone basique

### Frameworks web
- [fastapi_integration.py](examples/fastapi_integration.py) - API FastAPI complète avec webhooks
- [flask_integration.py](examples/flask_integration.py) - API Flask complète avec webhooks

Consultez [examples/README.md](examples/README.md) pour plus de détails et comment les exécuter.

## Logging

Le SDK configure automatiquement le logging à la **racine du projet utilisateur** :

```python
from shwary import configure_logging
import logging

# Mode debug pour voir toutes les requêtes/réponses
configure_logging(log_level=logging.DEBUG)

# Les logs s'écrivent dans :
# - Console (STDOUT)
# - Fichier: ./logs/shwary.log (rotation automatique à 10MB)
```

Sans données sensibles (clés API masquées).

## Exemples d'intégration

### FastAPI avec WebhooksShwary

```python
from fastapi import FastAPI, Request, HTTPException
from shwary import ShwaryAsync, WebhookPayload
import logging

app = FastAPI()

# Configuration du SDK Shwary
shwary = ShwaryAsync(
    merchant_id="your-merchant-id",
    merchant_key="your-merchant-key",
    is_sandbox=True
)

@app.post("/api/payments/initiate")
async def initiate_payment(phone: str, amount: float, country: str = "DRC"):
    """
    Initialise un paiement Shwary.
    
    Query params:
    - phone: numéro au format E.164 (ex: +243972345678)
    - amount: montant de la transaction
    - country: DRC, KE, UG (défaut: DRC)
    """
    try:
        async with shwary as client:
            payment = await client.initiate_payment(
                country=country,
                amount=amount,
                phone_number=phone,
                callback_url="https://yourapi.com/api/webhooks/shwary"
            )
        
        return {
            "success": True,
            "transaction_id": payment["id"],
            "status": payment["status"]
        }
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Shwary credentials invalid")
    except InsufficientFundsError:
        raise HTTPException(status_code=402, detail="Insufficient balance")
    except Exception as e:
        logging.error(f"Payment init failed: {e}")
        raise HTTPException(status_code=500, detail="Payment initiation failed")


@app.post("/api/webhooks/shwary")
async def handle_shwary_webhook(payload: WebhookPayload):
    """
    Reçoit les notifications de changement d'état de transactions.
    
    Shwary envoie une notification JSON lorsqu'une transaction change d'état.
    """
    logging.info(f"Webhook received: {payload.id} -> {payload.status}")
    
    if payload.status == "completed":
        # Transaction réussie - livrez le service
        logging.info(f"Payment completed: {payload.id}")
        # await deliver_service(payload.id)
    
    elif payload.status == "failed":
        # Transaction échouée
        logging.warning(f"Payment failed: {payload.id}")
        # await notify_user_failure(payload.id)
    
    return {"status": "ok"}


@app.get("/api/transactions/{transaction_id}")
async def get_transaction_status(transaction_id: str):
    """
    Récupère le statut d'une transaction.
    """
    try:
        async with shwary as client:
            tx = await client.get_transaction(transaction_id)
        
        return {
            "id": tx["id"],
            "status": tx["status"],
            "amount": tx["amount"]
        }
    
    except ShwaryAPIError as e:
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Transaction not found")
        raise HTTPException(status_code=500, detail="Error fetching transaction")
```

### Flask avec Shwary

```python
from flask import Flask, request, jsonify
from shwary import Shwary, ValidationError, AuthenticationError, ShwaryAPIError
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Client Shwary (synchrone pour Flask)
shwary_client = Shwary(
    merchant_id="your-merchant-id",
    merchant_key="your-merchant-key",
    is_sandbox=True
)

@app.route("/api/payments/initiate", methods=["POST"])
def initiate_payment():
    """
    Initialise un paiement Shwary.
    
    Body JSON:
    {
        "phone": "+243972345678",
        "amount": 5000,
        "country": "DRC"
    }
    """
    data = request.get_json()
    
    try:
        phone = data.get("phone")
        amount = data.get("amount")
        country = data.get("country", "DRC")
        
        if not all([phone, amount]):
            return jsonify({"error": "Missing phone or amount"}), 400
        
        payment = shwary_client.initiate_payment(
            country=country,
            amount=amount,
            phone_number=phone,
            callback_url="https://yourapi.com/api/webhooks/shwary"
        )
        
        return jsonify({
            "success": True,
            "transaction_id": payment["id"],
            "status": payment["status"]
        }), 200
    
    except ValidationError as e:
        app.logger.warning(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
    
    except AuthenticationError as e:
        app.logger.error(f"Auth error: {e}")
        return jsonify({"error": "Shwary authentication failed"}), 401
    
    except ShwaryAPIError as e:
        app.logger.error(f"API error: {e}")
        return jsonify({"error": f"Shwary error: {e.message}"}), e.status_code
    
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/webhooks/shwary", methods=["POST"])
def handle_shwary_webhook():
    """
    Reçoit les notifications de Shwary.
    """
    data = request.get_json()
    
    transaction_id = data.get("id")
    status = data.get("status")
    
    app.logger.info(f"Shwary webhook: {transaction_id} -> {status}")
    
    if status == "completed":
        # Transaction réussie
        app.logger.info(f"Payment completed: {transaction_id}")
        # deliver_service(transaction_id)
    
    elif status == "failed":
        # Transaction échouée
        app.logger.warning(f"Payment failed: {transaction_id}")
        # notify_user_failure(transaction_id)
    
    return jsonify({"status": "ok"}), 200


@app.route("/api/transactions/<transaction_id>", methods=["GET"])
def get_transaction_status(transaction_id):
    """Récupère le statut d'une transaction."""
    try:
        tx = shwary_client.get_transaction(transaction_id)
        
        return jsonify({
            "id": tx["id"],
            "status": tx["status"],
            "amount": tx["amount"]
        }), 200
    
    except ShwaryAPIError as e:
        if e.status_code == 404:
            return jsonify({"error": "Transaction not found"}), 404
        
        app.logger.error(f"Error fetching transaction: {e}")
        return jsonify({"error": "Server error"}), 500


@app.teardown_appcontext
def shutdown_shwary(exception=None):
    """Ferme le client Shwary à l'arrêt."""
    shwary_client.close()


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
```

### Configuration du Logging

Le SDK configure automatiquement le logging à la racine du projet. Pour augmenter le verbosity :

```python
import logging
from shwary import configure_logging

# Mode debug (affiche toutes les requêtes/réponses)
configure_logging(log_level=logging.DEBUG)

# Les logs sont écrits dans :
# - Console (STDOUT)
# - Fichier: ./shwary.log (rotation automatique à 10MB)
```

Les fichiers de log contiennent les détails des requêtes/réponses (sans données sensibles comme les clés API).

## Développement

Pour contribuer au SDK, consultez le fichier [CONTRIBUTING.md](./CONTRIBUTING.md)

### Licence

Distribué sous la licence MIT. Voir [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) pour plus d'informations.