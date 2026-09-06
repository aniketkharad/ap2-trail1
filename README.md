# Secure Agent Commerce (CineAgent) Monorepo

This repository houses the infrastructure, documentation, and agent implementations for autonomous commerce orchestration using open-source agentic commerce standards.

## Subprojects & Structure

- `agent_payments/`: The CineAgent booking service built with Google ADK, utilizing UCP and AP2.
- `gcloud_setup.md`: Step-by-step reproducible environment configuration, API provisioning, runtime execution, and teardown on Google Cloud.

## Commerce Protocols

- **UCP (Universal Commerce Protocol):** Standardizes merchant discovery, catalog search, and multi-merchant checkout orchestration across theater vendors.
- **AP2 (Agent Payments Protocol):** Manages secure, verifiable payment authorization using cryptographically signed mandates.

## Quickstart

Provision your Google Cloud environment, run the agent, and clean up by following the complete guide in [gcloud_setup.md](gcloud_setup.md).

## Agent Orchestration & Protocol Mapping

CineAgent acts as the primary orchestrator between user intent, UCP commerce discovery, and AP2 payment execution.

| Tool | Action Description | Protocol Layer |
| :--- | :--- | :--- |
| `discover_theaters` | Discovers theater merchants and capabilities | UCP (`/.well-known/ucp`) |
| `search_movies` | Aggregates and queries catalogs across vendors | MCP (JSON-RPC) |
| `get_movie_detail` | Retrieves showtimes and seat availability | MCP (JSON-RPC) |
| `create_checkout` | Initializes transaction session at target merchant | MCP (JSON-RPC) |
| `complete_purchase` | Signs AP2 Mandate and authorizes transaction (HITL Required) | AP2 + MCP |

> **Security Gate:** `complete_purchase` is wrapped with `FunctionTool(..., require_confirmation=True)` enforcing human approval before cryptographic mandate signing and fund transfer.

### Catalog Discovery Protocol Flow

1. **Merchant Introspection:** `discover_theaters` queries `GET /.well-known/ucp` on each target host to resolve capabilities, endpoint paths, and supported payment handlers.
2. **Catalog Aggregation:** `search_movies` issues JSON-RPC `search_catalog` calls across all registered merchants, merging multiple pricing and showtime variants into a unified product entity.
3. **Detail Resolution:** `get_movie_detail` issues a localized `lookup_catalog` query targeting a single merchant's catalog for seat layouts and availability.

### AP2 Dual-Mandate Security Lifecycle

1. **`CartMandate` (Merchant-to-Agent):** Cryptographically binds line items and total pricing. Prevents mid-transaction price drift or tampering.
2. **Human Authorization (HITL):** Agent triggers confirmation before proceeding to cryptographic signing.
3. **`PaymentMandate` (Agent/User-to-Merchant):** Proves user intent and authorizes fund deduction specifically against the verified `CartMandate`.
4. **Final Settlement:** Merchant MCP endpoint validates both signatures before ticket emission.
