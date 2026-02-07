"""
Exemple simple : Script Python synchrone avec Shwary.

Démontre comment initier un paiement et vérifier le statut en mode synchrone.
"""

import logging

from shwary import (
    AuthenticationError,
    InsufficientFundsError,
    Shwary,
    ShwaryAPIError,
    ValidationError,
)

# Configure le logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Exemple d'utilisation du SDK Shwary en mode synchrone."""

    # Crée le client avec les identifiants Shwary
    with Shwary(
        merchant_id="your-merchant-id",
        merchant_key="your-merchant-key",
        is_sandbox=True,  # True pour tests, False pour production
    ) as client:
        # --- EXEMPLE 1: Initier un paiement ---
        logger.info("Initiating payment...")

        try:
            payment = client.initiate_payment(
                country="DRC",
                amount=5000,  # 5000 CDF (minimum pour DRC)
                phone_number="+243972345678",
            )

            logger.info("Payment initiated successfully!")
            logger.info(f"   Transaction ID: {payment['id']}")
            logger.info(f"   Status: {payment['status']}")
            logger.info(f"   Sandbox: {payment.get('isSandbox')}")

            transaction_id = payment["id"]

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return

        except AuthenticationError:
            logger.error("Authentication failed - check merchant credentials")
            return

        except InsufficientFundsError:
            logger.error("Insufficient balance in merchant account")
            return

        except ShwaryAPIError as e:
            logger.error(f"API error {e.status_code}: {e.message}")
            return

        # --- EXEMPLE 2: Vérifier le statut de la transaction ---
        logger.info("\nFetching transaction status...")

        try:
            tx = client.get_transaction(transaction_id)

            logger.info("Transaction details:")
            logger.info(f"   ID: {tx['id']}")
            logger.info(f"   Status: {tx['status']}")
            logger.info(f"   Amount: {tx.get('amount')}")
            logger.info(f"   Phone: {tx.get('clientPhoneNumber')}")
            logger.info(f"   Created: {tx.get('createdAt')}")

        except ShwaryAPIError as e:
            if e.status_code == 404:
                logger.error(f"Transaction not found: {e.message}")
            else:
                logger.error(f"API error: {e.message}")
            return

        logger.info("\nAll operations completed successfully!")


if __name__ == "__main__":
    main()
