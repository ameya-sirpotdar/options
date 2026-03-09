
# Options Trading Agent System — MVP Plan with Engineering Epics

## Objective
Build an MVP system that can:
1. Poll options chain data for ~10 stocks
2. Store the data
3. Compute a Tradability Index
4. Return the best trade candidate
5. Allow on‑demand triggering for demos

Stack constraints:
- Language: Python
- Cloud: Azure
- Deployment: Azure Kubernetes Service (AKS)
- Scheduler / agents: LangGraph
- Storage: Azure Table Storage
- Frontend: Vue
- Source control: GitHub

---

# EPIC 1 — Core Infrastructure Setup

## Goal
Create the base cloud infrastructure, repo structure, and runtime environment.

### Story 1.1 – Create GitHub Repository
Tasks
- Create repo `options-agent-system`
- Add folders:
  - `/backend`
  - `/frontend`
  - `/infra`
- Add issue templates
- Add basic README

### Story 1.2 – Define Project Structure

/backend
&nbsp;&nbsp;api/
&nbsp;&nbsp;agents/
&nbsp;&nbsp;services/
&nbsp;&nbsp;models/

/frontend
&nbsp;&nbsp;vue-app/

/infra
&nbsp;&nbsp;terraform or bicep scripts

### Story 1.3 – Provision Azure Resources

Create:

- Azure Resource Group
- Azure Kubernetes Service (AKS)
- Azure Table Storage account

Recommended configuration

AKS
- 2 node pool
- Standard_B2s nodes

Storage Tables

optionsdata
sentimentdata
runlogs

### Story 1.4 – Storage Schema Design

optionsdata

PartitionKey = Ticker
RowKey = Timestamp

Example

PartitionKey = NVDA
RowKey = 2026-03-05T06:31

Columns

expiry
strike
delta
theta
iv
premium

runlogs

PartitionKey = RunDate
RowKey = RunID

### Story 1.5 – Kubernetes Deployment

Create

- Dockerfile for backend
- Kubernetes Deployment YAML
- Kubernetes Service YAML

Deploy Python API service.

---

# EPIC 2 — Backend API Layer

Framework: FastAPI

Endpoints

POST /poll/options
POST /poll/sentiment
GET /trades/best
GET /health

### Story 2.1 – Build FastAPI Service

Tasks

- Create FastAPI project
- Add health endpoint
- Add logging

### Story 2.2 – Implement On‑Demand Polling Endpoint

POST /poll/options

Input

tickers = ["NVDA","AAPL","MSFT"]

Action

- trigger LangGraph workflow
- call options agent

Return

status message

---

# EPIC 3 — Market Data Integration

## Goal
Pull options chains from Charles Schwab API.

### Story 3.1 – Authentication

Implement OAuth flow using

Client ID
Client Secret

Store credentials in Azure Key Vault.

### Story 3.2 – Options Chain Fetcher

For each ticker call

/marketdata/chains

Store returned contracts.

### Story 3.3 – Data Filtering

Filter contracts

- weekly expiration
- delta around 0.30
- put contracts only

---

# EPIC 4 — Data Storage Layer

Persist historical options data.

Fields

Ticker
Expiry
Strike
Delta
Theta
IV
Premium
Timestamp

Insert rows into Azure Table Storage.

### Story 4.2 – Run Logs

Log every polling run

runID
tickers processed
records stored

---

# EPIC 5 — Tradability Index Engine

### Story 5.1 – Metric Extraction

Extract

delta
theta
iv
premium

### Story 5.2 – Tradability Formula

score =
(theta_weight * theta)
+ (iv_weight * iv)
+ (premium_weight * premium)
- (delta_risk_weight * abs(delta-0.30))

### Story 5.3 – Ranking

Rank candidate trades.

Return best trade.

---

# EPIC 6 — LangGraph Agent Workflow

Agents

MarketSentimentAgent
OptionsDataAgent
MetricsAgent
TradabilityAgent

Flow

poll trigger
→ options agent
→ metrics agent
→ tradability agent
→ result

---

# EPIC 7 — Frontend Demo UI

Framework: Vue

Components

Button: Poll Market Data
Button: Calculate Trades
Table: Options Data
Card: Best Trade

---

# EPIC 8 — End‑to‑End Validation

Steps

1 trigger poll
2 store options data
3 compute tradability
4 return best trade

Example output

Ticker: NVDA
Strike: 820
Expiry: Friday
Delta: 0.29
Premium: 2.35
Tradability Score: 8.6

---

## GitHub Issues

| Epic | Issue |
|------|-------|
| Epic 5 — Tradability Index Engine | [#25](https://github.com/ameya-sirpotdar/options/issues/25) |
| Epic 6 — LangGraph Agent Workflow | [#27](https://github.com/ameya-sirpotdar/options/issues/27) |
| Epic 7 — Frontend Demo UI | [#29](https://github.com/ameya-sirpotdar/options/issues/29) |
