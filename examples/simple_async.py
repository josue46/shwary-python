"""
Exemple simple : Script Python asynchrone avec Shwary.

Démontre comment initier un paiement et vérifier le statut en mode asynchrone.
"""

import asyncio
import logging

from shwary import (
    AuthenticationError,
    InsufficientFundsError,
    RateLimitingError,
    ShwaryAPIError,
    ShwaryAsync,
    ShwaryError,
    ValidationError,
)

# Configure le logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def initiate_payment_example():
    """Exemple d'initiation de paiement en async."""

    # Crée le client asynchrone
    async with ShwaryAsync(
        merchant_id="your-merchant-id",
        merchant_key="your-merchant-key",
        is_sandbox=True,  # True pour tests, False pour production
    ) as client:
        logger.info("Initiating payment (async)...")

        try:
            payment = await client.initiate_payment(
                country="DRC",
                amount=5000,  # 5000 CDF (minimum pour DRC)
                phone_number="+243972345678",
            )

            logger.info("Payment initiated successfully!")
            logger.info(f"   Transaction ID: {payment['id']}")
            logger.info(f"   Status: {payment['status']}")

            return payment["id"]

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            raise

        except AuthenticationError:
            logger.error("Authentication failed - check merchant credentials")
            raise

        except InsufficientFundsError:
            logger.error("Insufficient balance in merchant account")
            raise

        except RateLimitingError:
            logger.error("Rate limited - waiting before retry...")
            raise

        except ShwaryAPIError as e:
            logger.error(f"API error {e.status_code}: {e.message}")
            raise


async def fetch_transaction_status(transaction_id: str):
    """Récupère le statut d'une transaction."""

    async with ShwaryAsync(
        merchant_id="your-merchant-id",
        merchant_key="your-merchant-key",
        is_sandbox=True,
    ) as client:
        logger.info(f"\nFetching transaction status for {transaction_id}...")

        try:
            tx = await client.get_transaction(transaction_id)

            logger.info("Transaction details:")
            logger.info(f"   ID: {tx['id']}")
            logger.info(f"   Status: {tx['status']}")
            logger.info(f"   Amount: {tx.get('amount')}")
            logger.info(f"   Phone: {tx.get('clientPhoneNumber')}")
            logger.info(f"   Created: {tx.get('createdAt')}")

            return tx

        except ShwaryAPIError as e:
            if e.status_code == 404:
                logger.error(f"Transaction not found: {e.message}")
            else:
                logger.error(f"API error: {e.message}")
            raise


async def main():
    """Exécute les exemples async."""

    try:
        # Initie le paiement
        transaction_id = await initiate_payment_example()

        # Attend un moment pour que le webhook soit reçu (simulation)
        await asyncio.sleep(2)

        # Récupère le statut
        await fetch_transaction_status(transaction_id)

        logger.info("\nAll async operations completed successfully!")

    except ShwaryError as e:
        logger.error(f"Shwary error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Exécute le code asynchrone
    asyncio.run(main())
