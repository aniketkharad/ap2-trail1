# Google Cloud Environment Setup

## Prerequisites

- A Google Cloud project with active billing enabled.
- Google Cloud Shell or a local terminal with authenticated `gcloud` access.

## 1. Project Selection & Authentication

Verify authentication and bind your session to your project:

```bash
# Verify active user credentials
gcloud auth list

# Set and verify active project
export PROJECT_ID="<YOUR_PROJECT_ID>"
gcloud config set project "$PROJECT_ID"
gcloud config get project
```

## 2. Enable Required APIs

Vertex AI is required for Gemini model routing via Google ADK. Enable the service:

```bash
gcloud services enable aiplatform.googleapis.com
```

## 3. Configure Environment Variables

Set the runtime variables required by the Google GenAI SDK:

```bash
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="global"
export GOOGLE_GENAI_USE_VERTEXAI="True"
```

## 4. Agent Runtime Initialization

Navigate to the agent directory and initialize the isolated virtual environment:

```bash
cd agent_payments
uv sync
source .venv/bin/activate
```

---

## 5. Runtime Execution & Verification

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

## 6. Teardown & Cost Management

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
