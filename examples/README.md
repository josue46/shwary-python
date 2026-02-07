# Exemples Shwary SDK

Ce dossier contient des exemples d'intégration complète avec le SDK Shwary.

## Fichiers

### 1. **simple_sync.py** - Script synchrone basique
Démontre comment :
- Initier un paiement en mode synchrone
- Récupérer le statut d'une transaction
- Gérer les erreurs

```bash
python examples/simple_sync.py
```

### 2. **simple_async.py** - Script asynchrone basique
Démontre comment :
- Initier un paiement en mode asynchrone
- Récupérer le statut d'une transaction
- Utiliser les context managers async

```bash
python examples/simple_async.py
```

### 3. **fastapi_integration.py** - Intégration FastAPI complète
API REST complète avec :
- Endpoint POST pour initier un paiement
- Endpoint POST pour recevoir les webhooks Shwary
- Endpoint GET pour vérifier le statut
- Gestion complète des erreurs
- Logging structuré

```bash
# Installez les dépendances
pip install fastapi uvicorn

# Lancez l'API
python -m uvicorn examples.fastapi_integration:app --reload
```

Endpoints disponibles :
- `POST /api/payments/initiate` - Initialiser un paiement
- `POST /api/webhooks/shwary` - Recevoir les webhooks
- `GET /api/transactions/{id}` - Récupérer le statut
- `GET /api/health` - Health check

### 4. **flask_integration.py** - Intégration Flask complète
API REST complète avec :
- Endpoint POST pour initier un paiement
- Endpoint POST pour recevoir les webhooks
- Endpoint GET pour vérifier le statut
- Gestion complète des erreurs

```bash
# Installez les dépendances
pip install flask

# Lancez l'API
python examples/flask_integration.py
```

Endpoints disponibles :
- `POST /api/payments/initiate` - Initialiser un paiement
- `POST /api/webhooks/shwary` - Recevoir les webhooks
- `GET /api/transactions/<id>` - Récupérer le statut
- `GET /api/health` - Health check

## Variables d'environnement

```bash
# Pour FastAPI et Flask
export SHWARY_MERCHANT_ID="your-merchant-id"
export SHWARY_MERCHANT_KEY="your-merchant-key"

# Pour Flask uniquement
export FLASK_DEBUG=True  # Mode développement
export PORT=5000        # Port d'écoute
```

## Tester les intégrations

### Avec curl

```bash
# Initier un paiement
curl -X POST http://localhost:5000/api/payments/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+243972345678",
    "amount": 5000,
    "country": "DRC"
  }'

# Récupérer le statut
curl http://localhost:5000/api/transactions/{transaction_id}
```

### Avec httpie

```bash
# Initier un paiement
http POST localhost:5000/api/payments/initiate \
  phone="+243972345678" \
  amount=5000 \
  country="DRC"

# Récupérer le statut
http GET localhost:5000/api/transactions/{transaction_id}
```

## Architecture

Tous les exemples suivent cette architecture :

```
┌─────────────┐
│   Client    │ (FastAPI/Flask/Python)
└──────┬──────┘
       │
       ├── POST /api/payments/initiate
       ├── GET  /api/transactions/{id}
       └── POST /api/webhooks/shwary
       │
┌──────▼──────────────────────-┐
│  Shwary SDK (python)         │
│  ├── Sync: Shwary            │
│  └── Async: ShwaryAsync      │
└──────┬───────────────────────┘
       │
┌──────▼──────────────────────┐
│     Shwary API              │
│  api.shwary.com/api/v1      │
└─────────────────────────────┘
```

## Bonnes pratiques

1. **Utiliser les variables d'environnement** pour les credentials
2. **Ajouter du logging** pour déboguer les problèmes
3. **Gérer toutes les exceptions** (ValidationError, AuthenticationError, etc.)
4. **Implémenter les webhooks** pour éviter le polling
5. **Utiliser async** pour les performances (FastAPI, Quart)
6. **Configurer les timeouts** appropriés pour votre cas d'usage

## Debugging

Augmentez le niveau de log pour plus de détails :

```python
import logging
from shwary import configure_logging

# Mode debug
configure_logging(log_level=logging.DEBUG)

# Les logs s'écriront dans shwary.log
```

## Support

Pour plus d'informations, consultez le [README principal](../README.md) ou les [tests unitaires](../src/shwary/tests/).
