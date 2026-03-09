# Options Trading Agent System

## Project Identity

An MVP system that polls options chain data, computes a Tradability Index, and surfaces the best trade candidate via a demo UI.

See [`docs/options_agent_mvp_epics.md`](docs/options_agent_mvp_epics.md) for the full plan.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Agent workflow | LangGraph |
| Storage | Azure Table Storage |
| Infrastructure | Azure / AKS |
| Frontend | Vue |
| Source control | GitHub |

## Planned Project Structure

```
/backend
  api/          # FastAPI routes
  agents/       # LangGraph agents (MarketSentimentAgent, OptionsDataAgent, MetricsAgent, TradabilityAgent)
  services/     # Business logic (options fetcher, tradability engine)
  models/       # Pydantic models / data schemas

/frontend
  vue-app/      # Vue frontend

/infra
  # Terraform or Bicep scripts for AKS + Azure Table Storage
```

## API Conventions

- Framework: FastAPI
- Follow RESTful conventions
- Return proper HTTP status codes (200, 404, 429, 500 — never wrap errors in HTTP 200)
- Core endpoints:
  - `POST /poll/options` — trigger LangGraph options polling workflow
  - `POST /poll/sentiment` — trigger sentiment agent
  - `GET /trades/best` — return top-ranked trade candidate
  - `GET /health` — health check

## Storage Schema

**optionsdata** table
- PartitionKey = Ticker (e.g. `NVDA`)
- RowKey = Timestamp (e.g. `2026-03-05T06:31`)
- Columns: expiry, strike, delta, theta, iv, premium

**runlogs** table
- PartitionKey = RunDate
- RowKey = RunID
- Columns: tickers processed, records stored

## Tradability Score Formula

```python
score = (
    (theta_weight * theta)
    + (iv_weight * iv)
    + (premium_weight * premium)
    - (delta_risk_weight * abs(delta - 0.30))
)
```

## Git Workflow

- Main branch: `main`
- All changes go on `feature/<name>` branches, then PR to `main`
- Never commit directly to `main`
- Delete source branches after merging

## CI/CD

The `autodev-agents` issue trigger workflow (`.github/workflows/issue-trigger.yml`) is active. It fires on new issues, issue comments, PR reviews, and PR review comments, then POSTs to `WORKER_URL/trigger` with the issue number. Requires `WORKER_URL` and `TRIGGER_API_KEY` secrets to be set in GitHub.

The `deploy.yml` workflow handles frontend deployment to Azure Static Web Apps. It includes a pre-flight validation step that fails fast with actionable error messages if any required GitHub secrets or variables are missing.

### Required GitHub Configuration for Frontend Deployment

Before the `deploy-frontend` job will succeed, the following must be configured in the GitHub repository:

**Secrets** (Settings → Secrets and variables → Actions → Secrets):
| Secret | Description |
|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Deployment token from the Azure Static Web App resource |

**Variables** (Settings → Secrets and variables → Actions → Variables):
| Variable | Description |
|---|---|
| `SWA_APP_LOCATION` | Path to the frontend app source (e.g. `frontend/vue-app`) |
| `SWA_OUTPUT_LOCATION` | Path to the built output directory (e.g. `dist`) |

See [`docs/setup/github-secrets-setup.md`](docs/setup/github-secrets-setup.md) for full setup instructions.

To validate your local environment and GitHub configuration before pushing, run:
```bash
bash scripts/validate-github-config.sh
```

## Development Guidelines

- Write unit tests for all new code
- Build and test locally before pushing (`uvicorn`, `pytest`)
- Store secrets (Schwab OAuth credentials, Azure keys) in Azure Key Vault — never in code or env files committed to the repo
- Python dependencies go in `backend/requirements.txt`
