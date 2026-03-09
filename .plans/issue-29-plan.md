# Implementation Plan — Issue #29: Frontend Demo UI

## Approach Overview

Scaffold a Vue 3 application (using Vite) inside `frontend/vue-app/`. The app will be a single-page layout with all components on one page. We will use the Vue Composition API and keep dependencies minimal (no heavy UI framework — plain CSS or minimal utility classes). Axios will handle HTTP calls to the backend. The app assumes the backend is running at a configurable base URL (via `.env`).

---

## Files to Create

### Project Scaffold
- `frontend/vue-app/package.json` — Vue 3 + Vite + Axios dependencies
- `frontend/vue-app/vite.config.js` — Vite config with proxy to backend (avoids CORS in dev)
- `frontend/vue-app/index.html` — HTML entry point
- `frontend/vue-app/.env.example` — `VITE_API_BASE_URL=http://localhost:8000`
- `frontend/vue-app/.gitignore` — node_modules, dist, .env

### Source Files
- `frontend/vue-app/src/main.js` — App entry, mounts Vue app
- `frontend/vue-app/src/App.vue` — Root component, single-page layout
- `frontend/vue-app/src/api/client.js` — Axios instance configured with base URL
- `frontend/vue-app/src/api/endpoints.js` — Named functions: `pollOptions()`, `calculateTrades()`
- `frontend/vue-app/src/components/InputPanel.vue` — Delta slider, expiry date picker, VIX display
- `frontend/vue-app/src/components/OptionsTable.vue` — Table rendering options data results
- `frontend/vue-app/src/components/BestTradeCard.vue` — Card showing best trade candidate
- `frontend/vue-app/src/composables/useMarketData.js` — Reactive state + logic for poll/calculate flow
- `frontend/vue-app/src/assets/main.css` — Minimal base styles

### Tests
- `frontend/vue-app/src/components/__tests__/InputPanel.spec.js`
- `frontend/vue-app/src/components/__tests__/OptionsTable.spec.js`
- `frontend/vue-app/src/components/__tests__/BestTradeCard.spec.js`
- `frontend/vue-app/vitest.config.js` — Vitest config for component tests

---

## Files to Modify

- `frontend/vue-app/.gitkeep` — Remove (replaced by actual scaffold)
- `frontend/.gitkeep` — Remove (directory now has content)
- `infra/k8s/deployment.yaml` — Note: may need a frontend container entry; defer to infra epic unless trivial
- `backend/main.py` — Verify CORS middleware allows `http://localhost:5173` (Vite dev server default)

---

## Implementation Steps

### Step 1 — Bootstrap Vue 3 + Vite project
```
cd frontend/vue-app
npm create vite@latest . -- --template vue
npm install axios
npm install -D vitest @vue/test-utils jsdom @vitejs/plugin-vue
```
Update `package.json` scripts: `dev`, `build`, `test`.

### Step 2 — Configure Vite proxy
In `vite.config.js`, add a proxy so `/api` calls forward to `http://localhost:8000` during development. This avoids CORS issues without requiring backend changes.

```js
server: {
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true }
  }
}
```

### Step 3 — API client layer
`src/api/client.js` — Axios instance with `baseURL` from `import.meta.env.VITE_API_BASE_URL`.

`src/api/endpoints.js`:
```js
export const pollOptions = (payload) => client.post('/poll/options', payload)
export const calculateTrades = (payload) => client.post('/calculate', payload)
// VIX: if no dedicated endpoint exists, fetch from poll response or display as static placeholder
```

> **Note:** The issue references a Calculate Trades endpoint but the backend router for it is not confirmed in the repo listing. The implementation will call `POST /calculate` and handle 404 gracefully with an error state. If the endpoint path differs, update `endpoints.js`.

### Step 4 — InputPanel component
`src/components/InputPanel.vue`:
- Delta: `<input type="range" min="0.10" max="0.50" step="0.01">` with live value display
- Expiry: `<input type="date">` (native date picker for simplicity)
- VIX: read-only display field, populated from poll response or prop
- Emits: `update:delta`, `update:expiry`; receives `vix` as prop

### Step 5 — useMarketData composable
`src/composables/useMarketData.js`:
```js
const delta = ref(0.30)
const expiry = ref('')
const vix = ref(null)
const optionsData = ref([])
const bestTrade = ref(null)
const loading = ref(false)
const error = ref(null)

async function poll() { ... } // calls pollOptions, sets optionsData + vix
async function calculate() { ... } // calls calculateTrades, sets bestTrade
```

### Step 6 — OptionsTable component
`src/components/OptionsTable.vue`:
- Accepts `rows` prop (array of option objects)
- Renders a `<table>` with columns: Symbol, Strike, Expiry, Delta, Bid, Ask, Score (or whatever fields the backend returns)
- Shows empty state message when no data

### Step 7 — BestTradeCard component
`src/components/BestTradeCard.vue`:
- Accepts `trade` prop (single object or null)
- Renders key fields: symbol, strike, expiry, score, recommendation
- Shows placeholder when no trade selected

### Step 8 — App.vue layout
Single-page layout:
```
<InputPanel> (top)
<div class="actions">
  <button @click="poll">Poll Market Data</button>
  <button @click="calculate" :disabled="!optionsData.length">Calculate Trades</button>
</div>
<OptionsTable :rows="optionsData" />
<BestTradeCard :trade="bestTrade" />
```
Wire up composable. Show loading spinner and error banner.

### Step 9 — CORS verification
In `backend/main.py`, confirm `CORSMiddleware` includes `http://localhost:5173`. Add if missing.

### Step 10 — README
Add `frontend/vue-app/README.md` with setup instructions: `npm install`, `npm run dev`, env var config.

---

## Test Strategy

### Unit / Component Tests (Vitest + @vue/test-utils)
- `InputPanel.spec.js`: slider emits correct delta value; date input emits expiry; VIX prop renders
- `OptionsTable.spec.js`: renders rows correctly; shows empty state when rows=[]
- `BestTradeCard.spec.js`: renders trade fields; shows placeholder when trade=null

### Manual E2E Validation
1. Start backend: `uvicorn backend.main:app --reload`
2. Start frontend: `npm run dev` in `frontend/vue-app`
3. Adjust delta slider → value updates in UI
4. Select expiry date
5. Click "Poll Market Data" → options table populates, VIX displays
6. Click "Calculate Trades" → Best Trade card populates

---

## Edge Cases to Handle

- Backend not reachable: show error banner, disable Calculate button
- Empty options response: show "No data returned" in table
- Calculate endpoint not yet implemented: show graceful error, don't crash
- VIX not in poll response: display "N/A" rather than blank
- Invalid date selection: disable Poll button until valid expiry chosen
- Delta slider at boundary values (0.10, 0.50): ensure these are valid and sent correctly

---

## Notes on Backend Endpoint Assumptions

- `POST /poll/options` — confirmed in `backend/api/poll.py`
- `POST /calculate` — **not confirmed** in repo listing; the frontend will call this endpoint but handle failure gracefully. If the endpoint is at a different path (e.g. `/score` or `/trades/calculate`), update `endpoints.js`.
- VIX value — assumed to be returned in the poll response payload. If it comes from a separate endpoint, add a `getVix()` call in the composable.
