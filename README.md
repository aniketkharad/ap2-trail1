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

[Block Diagram]

1. **`CartMandate` (Merchant-to-Agent):** Cryptographically binds line items and total pricing. Prevents mid-transaction price drift or tampering.
2. **Human Authorization (HITL):** Agent triggers confirmation before proceeding to cryptographic signing.
3. **`PaymentMandate` (Agent/User-to-Merchant):** Proves user intent and authorizes fund deduction specifically against the verified `CartMandate`.
4. **Final Settlement:** Merchant MCP endpoint validates both signatures before ticket emission.

## 8. Runtime Execution & Verification

To run CineAgent, both the mock merchant servers (ports `8081`, `8082`) and the ADK Web UI (port `8000`) must be active.

### Option A: Single-Terminal Setup (Cloud Shell)

1. **Start Mock Merchants in the Background:**
   ```bash
   cd agent_payments
   source .venv/bin/activate
   python merchants.py > merchants.log 2>&1 &
   ```

2. **Verify Merchant Health:**
   ```bash
   curl -s http://localhost:8081/.well-known/ucp | grep -o "Meridian Cinemas"
   ```

3. **Launch ADK Web UI:**
   ```bash
   cd ..
   export GOOGLE_CLOUD_PROJECT="$(gcloud config get-project)"
   export GOOGLE_CLOUD_LOCATION="global"
   export GOOGLE_GENAI_USE_VERTEXAI="True"

   adk web --allow_origins '*'
   ```

---

### Option B: Two-Terminal Setup

* **Terminal 1 (Merchants):**
  ```bash
  cd agent_payments
  source .venv/bin/activate
  python merchants.py
  ```

* **Terminal 2 (ADK UI):**
  ```bash
  source agent_payments/.venv/bin/activate
  export GOOGLE_CLOUD_PROJECT="$(gcloud config get-project)"
  export GOOGLE_CLOUD_LOCATION="global"
  export GOOGLE_GENAI_USE_VERTEXAI="True"

  adk web --allow_origins '*'
  ```

---

### Verification Test Flow

Access the Web UI URL and test the end-to-end UCP + AP2 flow:

1. **Catalog Search Across Merchants:**
   * **Prompt:** `What movies are playing?`
   * **Behavior:** CineAgent calls `discover_theaters` on `localhost:8081` and `localhost:8082`, aggregates showtimes via `search_movies`, and lists available screenings.

2. **Initiate Checkout:**
   * **Prompt:** `Book 2 tickets for Oppenheimer at 7 PM at Meridian`
   * **Behavior:** CineAgent initiates `create_checkout`. Meridian locks in the price and returns a signed `CartMandate`. The UI prompts for human-in-the-loop authorization.

3. **Authorize Transaction:**
   * **Prompt (Exact JSON Required):**
     ```json
     {"confirmed": true}
     ```
   * **Behavior:** CineAgent executes `complete_purchase`, cryptographically signs the `PaymentMandate`, submits dual mandates to the merchant MCP server, and issues ticket codes.

---

## 9. Teardown & Cost Management

Because this demo runs locally inside Cloud Shell, compute does not incur persistent infrastructure costs (e.g., no Compute Engine VMs or Cloud Run containers are left active). However, Vertex AI Gemini API calls are billed per token, and background processes must be terminated.

### Step 1: Stop Local Processes

* If running in foreground: Press `Ctrl+C` in both terminal sessions.
* If running in background (Option A):
  ```bash
  # Terminate mock merchant servers
  pkill -f "python merchants.py"

  # Exit virtual environment
  deactivate
  ```

### Step 2: Prevent Unintended Google Cloud Billing

* **Option 1: Retain project, disable API access (Zero ongoing cost):**
  If this is an existing project you use for other work, simply disable the Vertex AI API to prevent further API consumption:
  ```bash
  gcloud services disable aiplatform.googleapis.com
  ```

* **Option 2: Delete disposable scratch project (Irreversible):**
  > **WARNING:** Only execute this if you created a dedicated, disposable project exclusively for this codelab. This permanently deletes the project and all attached assets.

  ```bash
  gcloud projects delete "$GOOGLE_CLOUD_PROJECT"
  ```

