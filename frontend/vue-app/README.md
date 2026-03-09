# Frontend Vue App — Demo UI

Single-page placeholder frontend for end-to-end validation of the options trading pipeline.

## Overview

This Vue 3 + Vite application provides a minimal demo UI that exercises the full E2E flow:

1. Adjust the **Delta** slider (0.10 – 0.50)
2. Select an **expiry date** via the native date picker
3. Click **Poll Market Data** → the options table populates and the live VIX value is displayed
4. Click **Calculate Trades** → the best trade candidate card populates

## Project Structure

```
frontend/vue-app/
├── index.html
├── package.json
├── vite.config.js
├── vitest.config.js
├── .env.example
├── .gitignore
├── README.md
└── src/
    ├── main.js
    ├── App.vue
    ├── assets/
    │   └── main.css
    ├── api/
    │   ├── client.js
    │   └── endpoints.js
    ├── composables/
    │   └── useMarketData.js
    └── components/
        ├── InputPanel.vue
        ├── OptionsTable.vue
        ├── BestTradeCard.vue
        └── __tests__/
            ├── InputPanel.spec.js
            ├── OptionsTable.spec.js
            └── BestTradeCard.spec.js
```

## Prerequisites

- **Node.js** >= 18
- **npm** >= 9
- The **backend** running on `http://localhost:8000` (see `backend/` directory)

## Getting Started

### 1. Install dependencies

```bash
cd frontend/vue-app
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` if your backend runs on a different host or port. The default is:

```
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start the development server

```bash
npm run dev
```

The app will be available at **http://localhost:5173**.

API calls to `/api/*` are proxied to the backend via the Vite dev proxy configured in `vite.config.js`, so no CORS issues during local development.

### 4. Run tests

```bash
npm run test
```

Or in watch mode:

```bash
npm run test:watch
```

### 5. Build for production

```bash
npm run build
```

Output is placed in `dist/`.

## Component Reference

### `InputPanel`

Provides the three user controls:

| Control | Type | Range / Notes |
|---------|------|---------------|
| Delta | Range slider | 0.10 – 0.50, step 0.01 |
| Expiry | Date picker | Native `<input type="date">` |
| VIX | Read-only text | Populated after polling |

Emits:
- `poll` — user clicked **Poll Market Data**
- `calculate` — user clicked **Calculate Trades**

### `OptionsTable`

Renders the options chain returned by the poll endpoint as a sortable HTML table. Displays a loading state while the request is in flight and an empty-state message when no data is available.

### `BestTradeCard`

Displays the single best trade candidate returned by the calculate endpoint. Shows strike, expiry, premium, delta, and a simple risk/reward summary. Hidden until trade data is available.

## Composables

### `useMarketData`

Central reactive state manager. Exposes:

```js
const {
  delta,        // ref — current delta value
  expiry,       // ref — selected expiry date string
  vix,          // ref — latest VIX reading
  options,      // ref — array of polled option rows
  bestTrade,    // ref — best trade object or null
  isPolling,    // ref — loading flag for poll request
  isCalculating,// ref — loading flag for calculate request
  pollError,    // ref — error message from poll, or null
  calcError,    // ref — error message from calculate, or null
  pollOptions,  // async function — triggers poll API call
  calculateTrades, // async function — triggers calculate API call
} = useMarketData()
```

## API Layer

### `src/api/client.js`

Axios instance pre-configured with `baseURL` from `VITE_API_BASE_URL` and a 10-second timeout.

### `src/api/endpoints.js`

| Function | Method | Path | Description |
|----------|--------|------|-------------|
| `pollOptions(delta, expiry)` | `GET` | `/api/options/poll` | Fetch options chain + VIX |
| `calculateTrades(delta, expiry)` | `POST` | `/api/trades/calculate` | Compute best trade candidate |

## Backend CORS

The backend (`backend/main.py`) has been updated to include `http://localhost:5173` in its CORS allowed origins so that the Vite dev server can communicate with it directly (in addition to the proxied path).

## Linting & Formatting

```bash
# Lint
npm run lint

# Format
npm run format
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL for the backend API |

## Known Limitations

- This is a **demo / placeholder** UI intended for E2E validation only. It is not production-hardened.
- No authentication or authorisation is implemented.
- Error handling surfaces raw API error messages; no user-friendly error formatting is applied.
- The options table does not support pagination; large option chains may render slowly.