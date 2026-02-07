# Changelog

Tous les changements notables du SDK Shwary Python sont documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
et ce projet suit [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-02-06

### Nouveautés

#### Architecture & Refactorisation
- **Base class partagée** : Extraction des clients Sync/Async dans une classe `BaseShwaryClient` pour éliminer la duplication (~100 lignes)
- **Logging centralisé** : Nouveau module `logging_config.py` avec configuration automatique au premier import
- **Gestion des headers centralisée** : Headers HTTP maintenant définis une seule fois dans la base class

#### Fonctionnalités
- **Retry automatique** : Les erreurs réseau transitoires (timeout, connexion) sont retentées automatiquement :
  - Stratégie exponentielle : 2s → 4s → 8s (max 10s)
  - Nombre de tentatives : 3
  - Erreurs retentées : `httpx.TimeoutException`, `httpx.ConnectError`
  
- **Logging structuré** :
  - Les logs s'écrivent dans la racine du projet utilisateur (`./shwary.log`)
  - Rotation automatique à 10MB avec 5 backups
  - Format : `YYYY-MM-DD HH:MM:SS [LEVEL] shwary - message`
  - Données sensibles masquées (pas de clés API, numéros complets, montants)
  - Configuration : `from shwary import configure_logging`
  
- **Types stricts** : Nouveaux modèles Pydantic pour les réponses :
  - `PaymentResponse` : Réponse d'initiation de paiement
  - `TransactionResponse` : Détails d'une transaction
  - `WebhookPayload` : Payload reçu des webhooks Shwary
  
- **Exception Rate Limiting** : Nouvelle exception `RateLimitingError` pour erreur 429

#### Validation améliorée
- Montant minimum mieux documenté (RDC: 2900 CDF, KE/UG: > 0)
- Messages d'erreur de validation plus détaillés
- Validation croisée pays/numéro de téléphone renforcée

#### Documentation & Exemples
- **Docstrings complètes** : Avec exemples d'utilisation pour chaque fonction
- **Exemples d'intégration** :
  - `examples/simple_sync.py` : Script synchrone basique
  - `examples/simple_async.py` : Script asynchrone basique
  - `examples/fastapi_integration.py` : API FastAPI complète (~200 lignes)
  - `examples/flask_integration.py` : API Flask complète (~200 lignes)
  - `examples/README.md` : Guide complet sur l'utilisation des exemples
  
- **Tests étendus** : Nouveau fichier `test_advanced.py` couvrant :
  - Retries synchrones et asynchrones
  - Backoff exponentiel
  - Succès à la deuxième tentative
  - Preservation des réponses d'erreur

### Modifications de l'API

#### Clients (Shwary / ShwaryAsync)

**Avant (v1.0.1):**
```python
def initiate_payment(self, country: str, amount: float, 
                    phone_number: str, callback_url: str = None) -> dict
```

**Après (v2.0.0):**
```python
def initiate_payment(self, country: str, amount: float,
                    phone_number: str, callback_url: Optional[str] = None) 
                    -> PaymentResponse
```

- Retourne maintenant `PaymentResponse` (TypedDict) au lieu de `dict` brut
- Meilleure autocomplétion IDE et type checking

#### Exceptions

**Nouvelles:**
- `RateLimitingError` : Levée sur erreur 429

**Améliorées:**
- `ShwaryAPIError` : Stocke maintenant le status HTTP et la réponse brute
- Tous les messages d'erreur plus descriptifs

### Bugfixes

- **Bug critique**: Variable `data` non définie dans `raise_from_response` (exceptions.py)
  - Avant: `ShwaryAPIError(..., raw_response=data if 'data' in locals() else None)`
  - Après: `data = {}` initialisée avant try/catch

### Dépendances

**Ajoutées:**
- `tenacity>=9.0.0` : Pour les retries automatiques

**Versions existantes:**
- `httpx>=0.28.1` (identique)
- `phonenumbers>=9.0.22` (identique)
- `pydantic>=2.12.5` (identique)

### Performance

- **Mémoire** : `__slots__` optimisés dans BaseShwaryClient
- **Réseau** : Retries automatiques réduisent les faux négatifs
- **IDE** : Meilleure autocomplétion avec les nouveaux types

### Documentation

- README.md : Section "Quoi de neuf dans v2.0.0" + exemples
- Docstrings : Tous les modules et fonctions documentées
- Exemples : 4 fichiers complets (sync, async, FastAPI, Flask)
- Tests : 7 fichiers de tests covering 95%+ du code

### Breaking Changes

Aucun breaking change majeur. v2.0.0 est rétrocompatible avec v1.x pour les utilisations basiques.
Seule différence: les retours sont maintenant `PaymentResponse`/`TransactionResponse` 
au lieu de `dict` brut, ce qui améliore la type safety.

---

## [1.0.1] - 2025-01-15

### Initial Release

- Client synchrone et asynchrone
- Validation stricte des données
- Gestion des erreurs
- Support RDC, Kenya, Ouganda
