"""
Tests complets du SDK Shwary.

Les tests couvrent :
- Validation des données (locals)
- Erreurs API (401, 429, 500, etc.)
- Modèles Pydantic
- Clients synchrone et asynchrone
- Retry automatique
- Normalization de numéros
- Webhooks
"""

__all__ = [
    "test_client",
    "test_client_async",
    "test_validators",
    "test_schemas",
]
