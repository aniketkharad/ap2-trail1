"""Agent tools — each one wraps a UCP or AP2 operation."""

import asyncio
import json

from .ucp import UCPClient
from .ap2 import AP2Handler

# Initialize clients directly
_merchant_urls = ["http://localhost:8081", "http://localhost:8082"]
_ucp = UCPClient()
_ap2 = AP2Handler()


async def discover_theaters() -> str:
    """Discover available theater merchants and their capabilities via UCP."""
    theaters = []
    for url in _merchant_urls:
        info = await _ucp.discover(url)
        theaters.append(
            {
                "url": url,
                "name": info["name"],
                "capabilities": info["capabilities"],
                "payment_handlers": info["payment_handlers"],
            }
        )
    return json.dumps(theaters, indent=2)


async def search_movies(query: str = "") -> str:
    """Search for movies across all theaters. Use '' to browse all."""
    all_movies = {}
    for url, merchant in _ucp.merchants.items():
        result = await _ucp.mcp_call(url, "search_catalog", {"query": query})
        for product in result.get("products", []):
            mid = product["id"]
            if mid not in all_movies:
                all_movies[mid] = {
                    "id": mid,
                    "title": product["title"],
                    "categories": product.get("categories", []),
                    "theaters": {},
                }
            showtimes = []
            for v in product.get("variants", []):
                opts = {
                    o["name"]: o["value"]
                    for o in v.get("selected_options", [])
                }
                showtimes.append(
                    {
                        "id": v["id"],
                        "format": opts.get("format", "Standard"),
                        "time": opts.get("time", ""),
                        "price": v.get("price", {}),
                        "seats": v.get("availability", {}).get(
                            "seats_available", 0
                        ),
                    }
                )
            all_movies[mid]["theaters"][url] = {
                "name": merchant["name"],
                "showtimes": showtimes,
            }
    return json.dumps(list(all_movies.values()), indent=2)


async def get_movie_detail(movie_id: str, merchant_url: str) -> str:
    """Get detailed showtimes for a movie at a specific theater."""
    result = await _ucp.mcp_call(
        merchant_url, "lookup_catalog", {"product_id": movie_id}
    )
    return json.dumps(result, indent=2)


async def create_checkout(
    merchant_url: str, showtime_id: str, quantity: int = 1
) -> str:
    """Create a checkout session for tickets at a theater."""
    result = await _ucp.mcp_call(
        merchant_url,
        "create_checkout",
        {
            "checkout": {
                "line_items": [
                    {"item": {"id": showtime_id}, "quantity": quantity}
                ],
                "context": {"country": "US", "currency": "USD"},
            }
        },
    )
    return json.dumps(result, indent=2)


async def complete_purchase(
    checkout_id: str, merchant_url: str, payment_method: str = "card"
) -> str:
    """Complete purchase with AP2 payment authorization."""
    # 1. Retrieve CartMandate from active checkout session
    checkout = await _ucp.mcp_call(
        merchant_url, "get_checkout", {"checkout": {"id": checkout_id}}
    )
    cart_mandate = _ap2.process_cart_mandate(checkout)
    if not cart_mandate:
        return json.dumps({"error": "No cart mandate — checkout may have expired"})

    # 2. Create and sign PaymentMandate
    # In production, triggers user biometric/device auth via AP2 Wallet SDK.
    payment_mandate = _ap2.create_payment_mandate(cart_mandate, payment_method)

    # 3. Post dual mandates to merchant MCP endpoint to finalize purchase
    clean_port = merchant_url.rstrip("/").split(":")[-1]
    result = await _ucp.mcp_call(
        merchant_url,
        "complete_checkout",
        {
            "checkout": {
                "id": checkout_id,
                "payment": {
                    "instruments": [
                        {
                            "handler_id": f"card_{clean_port}",
                            "type": "card",
                        }
                    ],
                },
                "ap2": {"payment_mandate": payment_mandate},
            }
        },
    )
    return json.dumps(result, indent=2)
