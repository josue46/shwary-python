"""
Configuration du logging pour le SDK Shwary.

Le SDK configure automatiquement le logging au premier import pour écrire les logs
dans le projet de l'utilisateur.

Logger: "shwary"

**Où vont les logs:**

1. **Console** : STDOUT avec format standardisé
2. **Fichier** : shwary.log dans le répertoire courant, avec rotation automatique

**Format des logs:**

```
2025-02-06 10:30:45 [INFO] shwary - Request: /payment/sandbox/DRC
2025-02-06 10:30:46 [INFO] shwary - Response: /payment/sandbox/DRC - 200
```

**Exemple d'utilisation:**

```python
import logging
from shwary import Shwary, configure_logging

# Augmente la verbosité pour déboguer
configure_logging(log_level=logging.DEBUG)

# Les logs s'écrivent maintenant dans:
# - Console
# - ./shwary.log

with Shwary(...) as client:
    # Toutes les requêtes seront loggées
    payment = client.initiate_payment(...)
```

**Données loggées:**

- Endpoints appelés
- Status codes de réponse
- Transaction IDs (premiers 6 chars du téléphone pour validation)
- Pas de clés API
- Pas de numéros de téléphone complets
- Pas de montants sensibles au niveau DEBUG

"""

import logging
import logging.handlers
import sys
from pathlib import Path


def configure_logging(
    log_level: int = logging.INFO,
    log_file: str = "shwary.log",
    use_file_handler: bool = True,
) -> None:
    """
    Configure le logging pour le SDK Shwary.

    Crée un logger "shwary" qui écrit les logs de manière sécurisée dans :
    1. **Console (STDOUT)** : Pour développement et debugging
    2. **Fichier shwary.log** : Pour audit et production

    Cette fonction est appelée **automatiquement au premier import** du SDK.
    Vous pouvez la rappeler pour ajuster le niveau de log dynamiquement.

    **Important:** Les logs ne contiennent pas de données sensibles
    (clés API, numéros complets, montants).

    Args:
        log_level: Niveau minimal de log à capturer
                  - logging.DEBUG (10) : Tous les détails
                  - logging.INFO (20) : Informations principales
                  - logging.WARNING (30) : Seulement les avertissements/erreurs
                  - logging.ERROR (40) : Seulement les erreurs
                  - logging.CRITICAL (50) : Seulement les critiques
                  Par défaut: logging.INFO

        log_file: Chemin du fichier de log (relatif au répertoire courant)
                 Par défaut: "shwary.log"
                 Exemple: "../logs/shwary.log" ou "/var/log/shwary.log"

        use_file_handler: Si True, écrit aussi dans le fichier
                         Si False, logs console uniquement
                         Par défaut: True

    Raises:
        Exception: Si le fichier de log ne peut pas être créé
                  (permissions insuffisantes, chemin invalide)

    Example:
        Augmenter la verbosité:

        >>> import logging
        >>> from shwary import configure_logging
        >>> configure_logging(log_level=logging.DEBUG)

        Mode production (warnings only):

        >>> configure_logging(log_level=logging.WARNING)

        Logs dans un dossier custom:

        >>> configure_logging(log_file="/var/log/payment-api/shwary.log")

    Note:
        Le logger est configuré une seule fois. Les appels suivants
        mettent à jour le niveau de log des handlers existants
        mais n'ajoutent pas de nouveaux handlers.
    """
    logger = logging.getLogger("shwary")
    logger.setLevel(log_level)

    # Évite les handlers dupliqués si called plusieurs fois
    if logger.hasHandlers():
        # Met à jour le niveau sur les handlers existants
        for handler in logger.handlers:
            handler.setLevel(log_level)
        return

    # Format standardisé pour tous les logs
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] shwary - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Handler Console (STDOUT) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Handler Fichier (optionnel) ---
    if use_file_handler:
        try:
            # Résout le chemin relatif par rapport à la racine du projet utilisateur
            log_path: Path = (
                Path.cwd() / f"logs/{log_file}"
                if not Path(log_file).is_absolute()
                else Path(log_file)
            ).resolve()

            # Crée les répertoires si nécessaire
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Fichier rotatif: max 10MB par file, garde 5 backups
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,  # shwary.log, shwary.log.1, .2, ...
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # Log si configuration réussie
            logger.debug(f"Logging configured to file: {log_path}")

        except Exception as e:
            # Ne bloque pas le SDK si le logging file échoue
            # (permissions insuffisantes, disque plein, etc.)
            console_handler.emit(
                logging.LogRecord(
                    name="shwary",
                    level=logging.WARNING,
                    pathname="",
                    lineno=0,
                    msg=f"Could not configure file logging: {e}",
                    args=(),
                    exc_info=None,
                )
            )


# Configure le logging au premier import
configure_logging()
