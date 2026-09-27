# AI Penfight — Production Deployment Guide

This guide provides end-to-end instructions for deploying **AI Penfight** into production:
- **Backend API**: Hosted on [Render](https://render.com/) (FastAPI + Python)
- **Frontend App**: Hosted on [Vercel](https://vercel.com/) (Next.js + React)

---

## 1. Deployment Architecture

```text
┌─────────────────────────┐                 ┌─────────────────────────┐
│     Vercel Hosting      │                 │     Render Hosting      │
│                         │                 │                         │
│   Next.js 14 Frontend   │ ── HTTPS REST ─▶ │     FastAPI Backend     │
│ (ai-penfight.vercel.app)│                 │ (backend.onrender.com)  │
└─────────────────────────┘                 └───────────┬─────────────┘
                                                        │
                                                        ▼
                                            ┌─────────────────────────┐
                                            │       AI Engine         │
                                            │                         │
                                            │ LLM (OpenAI/Anthropic)  │
                                            │   or Fallback Engine    │
                                            └─────────────────────────┘
```

---

## 2. Deploying the Backend on Render

You can deploy the backend using either **Render Blueprints (IaC)**, **Native Python Web Service**, or **Docker**.

### Option A: Render Blueprint (Recommended — 1-Click IaC)

The repository includes a ready-to-use [`render.yaml`](../render.yaml) blueprint.

1. Log in to the [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** > **Blueprint**.
3. Connect your GitHub repository: `AI-PENFIGHT`.
4. Render will parse `render.yaml` and configure the `ai-penfight-backend` service.
5. Click **Apply**.
6. Under **Environment**, supply your secret `LLM_API_KEY` (if using OpenAI or Anthropic).

---

### Option B: Manual Web Service Setup

If you prefer to configure the service manually via the Render UI:

1. Click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the following service settings:
   - **Name**: `ai-penfight-backend`
   - **Region**: `Oregon (US West)` (or closest to your users)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (uses repo root)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free` or `Starter`
4. Expand **Advanced** and set:
   - **Health Check Path**: `/api/v1/health`
5. Under **Environment Variables**, add:

| Key | Value / Example | Notes |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Ensures consistent Python runtime |
| `PYTHONPATH` | `.` | Ensures `ai` and `backend` modules are resolved |
| `ENVIRONMENT` | `production` | Enables production mode |
| `LOG_LEVEL` | `info` | Logging verbosity |
| `ALLOWED_ORIGINS` | `https://ai-penfight.vercel.app` | Comma-separated Vercel frontend domains |
| `LLM_PROVIDER` | `openai` *(or `fallback` / `anthropic`)* | `fallback` requires zero API keys |
| `LLM_MODEL` | `gpt-4o-mini` | Recommended model |
| `LLM_API_KEY` | `sk-...` | Your LLM provider API key |
| `LLM_TIMEOUT` | `30.0` | Upstream request timeout (seconds) |
| `MAX_INPUT_LENGTH` | `5000` | Input character validation threshold |
| `MIN_INPUT_LENGTH` | `2` | Minimum character requirement |

6. Click **Create Web Service**.
7. Once deployed, note your service URL (e.g. `https://ai-penfight-backend.onrender.com`).

---

### Option C: Docker Deployment

Render also supports building directly from the provided [`Dockerfile`](../Dockerfile):
1. In Render, select **New +** > **Web Service**.
2. Select **Docker** as the runtime.
3. Render will automatically build the container and expose the web process on `$PORT`.

---

## 3. Deploying the Frontend on Vercel

1. Log in to the [Vercel Dashboard](https://vercel.com/).
2. Click **Add New…** > **Project**.
3. Import your GitHub repository: `AI-PENFIGHT`.
4. In the **Configure Project** screen:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click **Edit** and select `frontend` (or leave default if relying on root `vercel.json`).
5. Expand **Environment Variables** and add:

| Variable Name | Value | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://ai-penfight-backend.onrender.com` | URL of your deployed Render backend (no trailing slash) |

6. Click **Deploy**.
7. Vercel will build and deploy the Next.js frontend, generating your live domain (e.g., `https://ai-penfight.vercel.app`).

---

## 4. Connecting Frontend & Backend (CORS)

Once Vercel assigns your live domain (e.g., `https://ai-penfight-xyz.vercel.app`):

1. Go back to your **Render Dashboard** > `ai-penfight-backend` > **Environment**.
2. Update `ALLOWED_ORIGINS` to include your live Vercel domain:
   ```text
   ALLOWED_ORIGINS=https://ai-penfight.vercel.app,https://ai-penfight-xyz.vercel.app
   ```
3. Render will automatically redeploy the backend with the new CORS origin headers.

---

## 5. Verifying Your Deployment

### 1. Test Backend Health Check
```bash
curl -i https://ai-penfight-backend.onrender.com/api/v1/health
```
**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "ai_provider": "openai",
  "ai_available": true
}
```

### 2. Test Live Analysis Endpoint
```bash
curl -X POST https://ai-penfight-backend.onrender.com/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"input": "Decentralized microgrids dramatically improve disaster resilience."}'
```
**Expected Response (200 OK):**
```json
{
  "success": true,
  "analysisId": "an_...",
  "analysis": "...",
  "feedback": "...",
  "recommendations": [...],
  "score": { "overall_score": 82.5 },
  "createdAt": "..."
}
```

### 3. Verify Frontend Application
1. Open your Vercel URL in a browser (`https://ai-penfight.vercel.app`).
2. Paste sample debate text into the analysis field.
3. Click **Mark it up** and confirm that feedback and analysis are displayed.

---

## 6. Continuous Integration (CI/CD)

The repository includes GitHub Actions workflows under `.github/workflows/`:
- **`backend-ci.yml`**: Automatically runs on PRs/pushes, installing dependencies and running the complete test suite (`pytest`).
- **`frontend-ci.yml`**: Validates Next.js build compilation across Node.js versions.
