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
