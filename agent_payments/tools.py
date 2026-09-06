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


# Stubs to satisfy agent.py imports until subsequent steps implement them
async def create_checkout(*args, **kwargs) -> str:
    """Stub: Initialize checkout session."""
    raise NotImplementedError("Checkout flow not implemented yet.")


async def complete_purchase(*args, **kwargs) -> str:
    """Stub: Authorize and complete payment via AP2."""
    raise NotImplementedError("AP2 mandate completion not implemented yet.")
