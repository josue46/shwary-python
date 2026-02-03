# Shwary Python SDK

[![PyPI version](https://img.shields.io/pypi/v/shwary-python.svg)](https://pypi.org/project/shwary-python/)
[![Python versions](https://img.shields.io/pypi/pyversions/shwary-python.svg)](https://pypi.org/project/shwary-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Shwary Python** est une bibliothèque cliente moderne, asynchrone et performante (non officielle)  pour l'intégration de l'API [Shwary](https://shwary.com). Elle permet d'initier des paiements Mobile Money en **RDC**, au **Kenya** et en **Ouganda** avec une validation stricte des données avant l'envoi.



## Caractéristiques

* **Gestion d'erreurs native** : Pas besoin de vérifier les `status_code` manuellement. Le SDK lève des exceptions explicites (`AuthenticationError`, `ValidationError`, etc.).
* **Async-first** : Construit sur `httpx` pour des performances optimales (Pooling de connexions).
* **Dual-mode** : Support complet des modes Synchrone et Asynchrone.
* **Validation Robuste** : Vérification des numéros (E.164) et des montants minimums (ex: 2900 CDF pour la RDC).
* **Type-safe** : Basé sur Pydantic V2 pour une autocomplétion parfaite dans votre IDE.
* **Ultra-rapide** : Optimisé avec `uv` et `__slots__` pour minimiser l'empreinte mémoire.

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
### Initier un paiement (Async)
Le SDK gère les erreurs pour vous. Enveloppez simplement votre appel dans un bloc `try...except`.

```python
import asyncio
from shwary import ShwaryAsync

async def main():
    async with ShwaryAsync(
        merchant_id="votre-uuid",
        merchant_key="votre-cle-secrete",
        is_sandbox=True
    ) as client:
        try:
            # Le SDK lève une exception si l'API répond avec une erreur
            payment = await client.initiate_payment(
                country="DRC",
                amount=5000,
                phone_number="+243972345678",
                callback_url="[https://votre-site.com/webhooks/shwary](https://votre-site.com/webhooks/shwary)"
            )
            print(f"ID Transaction: {payment['id']}")
        except Exception as e:
            print(f"Le paiement a échoué: {e}")

asyncio.run(main())
```

### Initier un paiement (Sync)
```python
from shwary import Shwary

with Shwary(merchant_id="...", merchant_key="...", is_sandbox=False) as client:
    response = client.initiate_payment(
        country="KE",
        amount=150.5,
        phone_number="+254700000000"
    )
```

## Vérifier une transaction
Si vous n'avez pas reçu de webhook ou souhaitez vérifier le statut actuel :

```python
# Mode Synchrone
from shwary import Shwary

with Shwary(merchant_id="...", merchant_key="...") as client:
    tx = client.get_transaction("votre-id-transaction")
    print(f"Statut actuel : {tx['status']}")
```

## Validation par pays
Le SDK applique les règles métiers de Shwary localement pour économiser des appels réseau :

| Pays | Code | Devise | Montant Min. |
| :--- | :--- | :--- | :--- |
| RDC | DRC | CDF | 2900 |
| Kenya | KE | KES | > 0 |
| Ouganda | UG | UGX | > 0 |

## Gestion des Webhooks (Callbacks)
Lorsque le statut d'un paiement change (ex: pending -> completed), Shwary envoie un POST JSON à votre callbackUrl. Voici comment traiter la charge utile avec les modèles du SDK (exemple FastAPI) :

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/webhooks/shwary")
async def shwary_webhook(data: dict):
    # Shwary envoie le même format que la réponse initiate_payment
    status = data.get("status")
    transaction_id = data.get("id")
    
    if status == "completed":
        # Livrez votre service ici
        pass
    
    return {"status": "ok"}
```

## Gestion des Erreurs
Le SDK transforme les erreurs HTTP en exceptions Python. Vous n'avez pas besoin de vérifier manuellement les codes de statut, gérez simplement les exceptions :

| Exception | Cause |
| :--- | :--- |
| **ValidationError** | Données invalides (ex: montant < 2900 CDF en RDC, numéro mal formé). |
| **AuthenticationError** | Identifiants `merchant_id` ou `merchant_key` incorrects. |
| **ShwaryAPIError** | Erreur côté serveur Shwary ou problème réseau. |
| **ShwaryError** | Classe de base pour toutes les exceptions du SDK. |


```python
from shwary.exceptions import ValidationError, AuthenticationError, ShwaryAPIError

try:
    client.initiate_payment(...)
except ValidationError as e:
    # Erreur de format téléphone ou montant insuffisant
    print(f"Données invalides : {e}")
except AuthenticationError:
    # Identifiants merchant_id / merchant_key invalides
    print("Erreur d'authentification Shwary")
except ShwaryAPIError as e:
    # Autres erreurs API (404, 500, etc.)
    print(f"Erreur API {e.status_code}: {e.message}")
```

## Développement

Pour contribuer au SDK :

    1. Installez uv : curl -LsSf https://astral.sh/uv/install.sh | sh

    2. Installez les dépendances : uv sync

    3. Lancez les tests : uv run pytest

### Licence

Distribué sous la licence MIT. Voir [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) pour plus d'informations.