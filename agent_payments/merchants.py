"""Mock UCP merchant servers — two theaters with different capabilities."""

import uuid
import time
import multiprocessing
from datetime import datetime, timezone, timedelta

import uvicorn
from fastapi import FastAPI

# ── Theater data ────────────────────────────────────────────

THEATERS = {
    8081: {
        "name": "Meridian Cinemas",
        "movies": [
            {
                "id": "opp",
                "title": "Oppenheimer",
                "categories": ["Drama", "History"],
                "showtimes": [
                    {"id": "st_opp_7pm_imax", "format": "IMAX", "time": "7:00 PM", "price": 2200, "seats": 45},
                    {"id": "st_opp_930pm", "format": "Standard", "time": "9:30 PM", "price": 1500, "seats": 80},
                ],
            },
            {
                "id": "dune3",
                "title": "Dune: Part Three",
                "categories": ["Sci-Fi", "Action"],
                "showtimes": [
                    {"id": "st_dune_8pm_imax", "format": "IMAX", "time": "8:00 PM", "price": 2200, "seats": 30},
                ],
            },
        ],
        "discounts": {},
    },
    8082: {
        "name": "StarLight Theaters",
        "movies": [
            {
                "id": "opp",
                "title": "Oppenheimer",
                "categories": ["Drama", "History"],
                "showtimes": [
                    {"id": "st_opp_6pm_atmos", "format": "Dolby Atmos", "time": "6:00 PM", "price": 1800, "seats": 60},
                ],
            },
            {
                "id": "spider",
                "title": "Spider-Verse",
                "categories": ["Animation", "Action"],
                "showtimes": [
                    {"id": "st_spider_4pm", "format": "Standard", "time": "4:00 PM", "price": 1200, "seats": 100},
                ],
            },
        ],
        "discounts": {},
    },
}


def create_app(port):
    theater = THEATERS[port]
    app = FastAPI()
    sessions = {}

    # ── UCP Discovery endpoint ──────────────────────────────
    @app.get("/.well-known/ucp")
    def discovery():
        caps = {
            "dev.ucp.shopping.catalog.search": [{"version": "2026-01-15"}],
            "dev.ucp.shopping.catalog.lookup": [{"version": "2026-01-15"}],
            "dev.ucp.shopping.checkout": [{"version": "2026-01-15"}],
            "dev.ucp.shopping.ap2_mandate": [{"version": "2026-01-15"}],
        }

        return {
            "ucp": {
                "version": "2026-01-15",
                "services": {
                    "dev.ucp.shopping": [
                        {"version": "2026-01-15", "transport": "mcp",
                         "endpoint": f"http://localhost:{port}/mcp"}
                    ]
                },
                "capabilities": caps,
                "payment_handlers": {
                    "com.example.card": [
                        {"id": f"card_{port}", "version": "2026-01-15",
                         "available_instruments": [{"type": "card"}], "config": {}}
                    ]
                },
            }
        }

    # ── MCP JSON-RPC endpoint ───────────────────────────────
    @app.post("/mcp")
    def mcp(body: dict):
        tool = body["params"]["name"]
        args = body["params"].get("arguments", {})
        rid = body.get("id", "1")

        if tool == "search_catalog":
            q = args.get("query", "").lower()
            hits = [m for m in theater["movies"]
                    if not q or q in m["title"].lower()
                    or any(q in c.lower() for c in m["categories"])]
            return _ok(rid, {"products": [_product(m) for m in hits]})

        if tool == "lookup_catalog":
            mid = args.get("product_id") or (args.get("ids", [None])[0])
            movie = next((m for m in theater["movies"] if m["id"] == mid), None)
            if not movie:
                return _err(rid, "Not found")
            return _ok(rid, {"products": [_product(movie)]})

        if tool == "create_checkout":
            co = args.get("checkout", {})
            sid = f"chk_{uuid.uuid4().hex[:12]}"
            items, subtotal = [], 0
            for li in co.get("line_items", []):
                st = _find_showtime(li["item"]["id"])
                if not st:
                    continue
                mv = _find_movie(li["item"]["id"])
                qty = li.get("quantity", 1)
                amt = st["price"] * qty
                subtotal += amt
                items.append({
                    "id": f"li_{uuid.uuid4().hex[:8]}",
                    "item": {
                        "id": st["id"],
                        "title": f"{mv['title']} — {st['format']} {st['time']}",
                        "price": st["price"],
                    },
                    "quantity": qty,
                    "totals": [{"type": "subtotal", "amount": amt}],
                })
            tax = int(subtotal * 0.08)
            total = subtotal + tax
            session = {
                "id": sid,
                "status": "ready_for_complete",
                "currency": "USD",
                "line_items": items,
                "totals": [
                    {"type": "subtotal", "display_text": "Subtotal", "amount": subtotal},
                    {"type": "tax", "display_text": "Tax", "amount": tax},
                    {"type": "total", "display_text": "Total", "amount": total},
                ],
                "metadata": {"theater_name": theater["name"]},
                "ap2": {
                    "cart_mandate": {
                        "contents": {
                            "id": sid,
                            "merchant_name": theater["name"],
                            "total": {
                                "label": "Total",
                                "amount": {"currency": "USD", "value": total / 100},
                            },
                            "cart_expiry": (
                                datetime.now(timezone.utc) + timedelta(minutes=10)
                            ).isoformat(),
                        },
                        "merchant_authorization": f"mock_merchant_sig_{sid}",
                    }
                },
            }
            sessions[sid] = session
            return _ok(rid, session)

        if tool == "get_checkout":
            sid = args.get("checkout", {}).get("id") or args.get("id")
            return _ok(rid, sessions.get(sid, {"error": "not_found"}))

        if tool == "complete_checkout":
            co = args.get("checkout", {})
            sid = co.get("id")
            session = sessions.get(sid)
            if not session:
                return _err(rid, "Not found")
            session["status"] = "completed"
            session["order"] = {
                "id": f"ord_{uuid.uuid4().hex[:8]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "tickets": [
                    {
                        "movie": li["item"]["title"],
                        "quantity": li["quantity"],
                        "ticket_code": uuid.uuid4().hex[:8].upper(),
                    }
                    for li in session["line_items"]
                ],
            }
            session["ap2"]["payment_mandate_verified"] = True
            return _ok(rid, session)

        return _err(rid, f"Unknown tool: {tool}")

    def _ok(rid, result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def _err(rid, msg):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": msg}}

    def _product(movie):
        return {
            "id": movie["id"],
            "title": movie["title"],
            "categories": movie["categories"],
            "variants": [
                {
                    "id": st["id"],
                    "selected_options": [
                        {"name": "format", "value": st["format"]},
                        {"name": "time", "value": st["time"]},
                    ],
                    "price": {"amount": st["price"], "currency": "USD"},
                    "availability": {"available": True, "seats_available": st["seats"]},
                }
                for st in movie["showtimes"]
            ],
        }

    def _find_showtime(sid):
        return next(
            (st for m in theater["movies"] for st in m["showtimes"] if st["id"] == sid),
            None,
        )

    def _find_movie(sid):
        return next(
            (m for m in theater["movies"] for st in m["showtimes"] if st["id"] == sid),
            None,
        )

    return app


def _run(port):
    uvicorn.run(create_app(port), host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    for port in THEATERS:
        multiprocessing.Process(target=_run, args=(port,), daemon=True).start()
    print("Merchants running: Meridian (:8081), StarLight (:8082)")
    print("Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
