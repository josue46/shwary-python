# Contributing to Shwary Python SDK

Merci de votre intérêt pour contribuer au SDK Shwary Python!

Ce document explique comment configurer l'environnement de développement et soumettre vos contributions.

## Table des matières

1. [Installation de développement](#installation-de-développement)
2. [Tests](#tests)
3. [Lint et formatage](#lint-et-formatage)
4. [Soumettre une PR](#soumettre-une-pr)
5. [Conventions de code](#conventions-de-code)

## Installation de développement

### Prérequis

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (gestionnaire de packages moderne)

### Étapes

```bash
# Clone le répertoire
git clone https://github.com/josue46/shwary-python.git
cd shwary-python

# Crée l'environnement et installe les dépendances
uv sync

# Active l'environnement (optionnel si vous utilisez `uv run`)
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows
```

## Tests

### Lancer tous les tests

```bash
# Mode simple
uv run pytest

# Avec couverture de code
uv run pytest --cov=shwary --cov-report=html

# En verbose
uv run pytest -v

# Un fichier spécifique
uv run pytest src/shwary/tests/test_client.py
```

### Fichiers de tests

- `test_client.py` : Tests du client synchrone
- `test_client_async.py` : Tests du client asynchrone
- `test_schemas.py` : Tests des validateurs Pydantic
- `test_validators.py` : Tests spécifiques de validation
- `test_advanced.py` : Tests des retries et logging

### Écrire des tests

```python
# Exemple avec respx (mock HTTP)
import respx
from httpx import Response
from shwary import Shwary

@respx.mock
def test_my_feature(client):
    respx.post("https://api.shwary.com/...").mock(
        return_value=Response(200, json={"id": "123"})
    )
    
    result = client.initiate_payment(...)
    assert result["id"] == "123"
```

## Lint et formatage

### Ruff (linter + formateur)

```bash
# Vérifier les erreurs
uv run ruff check src/

# Corriger automatiquement
uv run ruff check --fix src/

# Formater le code
uv run ruff format src/
```

### Configuration

Le projet utilise la configuration Ruff dans `pyproject.toml`:

```toml
[tool.ruff]
line-length = 88
select = ["E", "F", "I"]  # Errors, Flakes, Import sorting
```

## Soumettre une PR

### Avant de soumettre

1. **Fork le projet** sur GitHub
2. **Crée une branche** pour ta feature
   ```bash
   git checkout -b feature/my-amazing-feature
   ```

3. **Fais tes changements** et écris des tests
4. **Assure-toi que les tests passent**
   ```bash
   uv run pytest
   ```

5. **Formatte ton code**
   ```bash
   uv run ruff format src/
   uv run ruff check --fix src/
   ```

6. **Commit avec des messages clairs**
   ```bash
   git commit -m "feat: add retry mechanism for network timeouts"
   ```

7. **Push et crée une PR**
   ```bash
   git push origin feature/my-amazing-feature
   ```

### Template de PR

```markdown
## Description
Brève description de ce que fait cette PR.

## Type de changement
- [ ] Bug fix (correction)
- [ ] New feature (nouvelle fonctionnalité)
- [ ] Breaking change (changement non rétrocompatible)
- [ ] Documentation

## Changements
- Point 1
- Point 2

## Tests ajoutés
- [ ] Tests unitaires ajoutés
- [ ] Tests couvrent les cas normaux et d'erreur
- [ ] Tous les tests passent

## Checklist
- [ ] Code suit les conventions du projet
- [ ] Tests passent (`uv run pytest`)
- [ ] Code formaté (`uv run ruff format`)
- [ ] Docstring ajoutées si nécessaire
```

## Conventions de code

### Style

Cette codebase suit le style Python moderne (PEP 8) avec Ruff:

```python
# Bon
def initiate_payment(
    country: str,
    amount: float,
    phone_number: str,
) -> PaymentResponse:
    """Documentation."""
    return response

# Mauvais
def initiate_payment(country,amount,phone_number):
    # Comment
    return response
```

### Docstrings

Utilisez le format Google pour les docstrings:

```python
def prepare_payment_request(
    country: str,
    amount: float,
) -> tuple[str, dict]:
    """
    Brève description.
    
    Description plus longue si nécessaire.
    
    Args:
        country: Description du paramètre
        amount: Description du paramètre
    
    Returns:
        Description du retour
    
    Raises:
        ValidationError: Quand c'est levé
    
    Example:
        >>> result = function(...)
        >>> result
        {...}
    """
    pass
```

### Imports

Les imports doivent être triés lexicographiquement:

```python
# Bon
import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel

from .schemas import PaymentPayload

# Mauvais
import logging
from datetime import datetime
import asyncio
from pydantic import BaseModel
from .schemas import PaymentPayload
import httpx
```

### Type hints

Toujours utiliser les type hints:

```python
# Bon
def initiate_payment(
    country: str,
    amount: float,
) -> PaymentResponse:
    pass

# Mauvais
def initiate_payment(country, amount):
    pass
```

### Logging

Utilisez le logger du SDK:

```python
from logging import getLogger

logger = getLogger("shwary")

logger.info("Something happened")
logger.error("An error occurred", exc_info=True)
```

### Exceptions

Créez des exceptions significatives:

```python
# Bon
raise ValidationError("Phone number must be in E.164 format")

# Mauvais
raise Exception("Error")
```

## Processus de Release

La maintenances suit [Semantic Versioning](https://semver.org/):

- **Major** (x.0.0) : Breaking changes
- **Minor** (2.1.0) : Nouvelles fonctionnalités rétrocompatibles
- **Patch** (2.0.1) : Bug fixes

## Questions?

Si vous avez des questions, créez une issue ou contactez les mainteneurs.

Merci!
