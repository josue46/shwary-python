"""
Clients Shwary pour l'API de paiement.

Deux clients disponibles:
- Shwary: Client synchrone pour applications standards (Flask, Django, scripts)
- ShwaryAsync: Client asynchrone pour applications async (FastAPI, Quart, etc.)

Exemple synchrone:
    from shwary import Shwary
    
    with Shwary(merchant_id="...", merchant_key="...") as client:
        payment = client.initiate_payment(
            country="DRC",
            amount=5000,
            phone_number="+243972345678"
        )
        print(f"Transaction ID: {payment['id']}")

Exemple asynchrone:
    import asyncio
    from shwary import ShwaryAsync
    
    async def process_payment():
        async with ShwaryAsync(merchant_id="...", merchant_key="...") as client:
            payment = await client.initiate_payment(
                country="DRC",
                amount=5000,
                phone_number="+243972345678"
            )
            print(f"Transaction ID: {payment['id']}")
    
    asyncio.run(process_payment())
"""

from .async_client import ShwaryAsync
from .sync import Shwary

__all__ = ("Shwary", "ShwaryAsync")