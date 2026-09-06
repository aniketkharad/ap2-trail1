# Secure Agent Commerce (CineAgent) Monorepo

This repository houses the infrastructure, documentation, and agent implementations for autonomous commerce orchestration using open-source agentic commerce standards.

## Subprojects & Structure

- `agent_payments/`: The CineAgent booking service built with Google ADK, utilizing UCP and AP2.
- `gcloud_setup.md`: Step-by-step reproducible environment configuration and API provisioning on Google Cloud.

## Commerce Protocols

- **UCP (Universal Commerce Protocol):** Standardizes merchant discovery, catalog search, and multi-merchant checkout orchestration across theater vendors.
- **AP2 (Agent Payments Protocol):** Manages secure, verifiable payment authorization using cryptographically signed mandates.

## Quickstart

1. Provision Google Cloud resources and enable required APIs per [gcloud_setup.md](gcloud_setup.md).
2. Set up the agent runtime:
   ```bash
   cd agent_payments
   uv sync
   source .venv/bin/activate
   ```
