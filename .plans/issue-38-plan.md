# Implementation Plan: Fix Deployment Gaps Before E2E Validation

## Approach Overview

Three targeted fixes across backend configuration, frontend API client, and Kubernetes manifests. Each change is independent and low-risk individually, but together they unblock end-to-end deployment validation. We will audit the actual codebase to determine ground truth before making changes.

---

## Gap 1: Audit and Fix `backend/.env.example`

### Investigation
- Read `backend/config.py` to identify all env vars the application actually reads (via `os.environ`, `os.getenv`, Pydantic `BaseSettings`, etc.)
- Read `backend/services/schwab_auth.py`, `backend/services/azure_table_service.py`, and other service files for any additional env var reads
- Compare against current `backend/.env.example`

### Changes
- Remove stale/incorrect variable names from `backend/.env.example`
- Add any missing variables that the app actually reads
- Ensure every variable has a descriptive comment explaining its purpose
- Use placeholder values (e.g. `YOUR_VALUE_HERE`) for secrets, real defaults for non-sensitive config

### Expected Variables (to be confirmed by audit)
Based on the service files present:
- `SCHWAB_CLIENT_ID` / `SCHWAB_CLIENT_SECRET` / `SCHWAB_REDIRECT_URI` (schwab_auth.py)
- `AZURE_STORAGE_CONNECTION_STRING` or `AZURE_STORAGE_ACCOUNT_KEY` + `AZURE_STORAGE_ACCOUNT_NAME` (azure_table_service.py)
- `AZURE_TABLE_NAME` or similar table config
- Any API keys, ports, or feature flags read in config.py or main.py

---

## Gap 2: Fix Frontend `client.js` to Use `VITE_API_BASE_URL`

### Investigation
- Read `frontend/vue-app/src/api/client.js` to see the current env var name being read
- Read `frontend/vue-app/.env.example` to see what's documented
- Read `frontend/vue-app/vite.config.js` to confirm Vite env var handling

### Changes to `frontend/vue-app/src/api/client.js`
- Replace any hardcoded URL or incorrect env var reference with:
  ```js
  const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  ```
- Ensure the axios/fetch client uses `BASE_URL` as the base URL
- Fallback to localhost for local development

### Changes to `frontend/vue-app/.env.example`
- Ensure `VITE_API_BASE_URL=https://your-backend-url` is present and documented

---

## Gap 3: Add `secretKeyRef` Entries to K8s `deployment.yaml`

### Investigation
- Read `infra/k8s/deployment.yaml` to see current container spec
- Cross-reference with `backend/.env.example` (after Gap 1 fix) and `backend/config.py` for required secrets

### Changes to `infra/k8s/deployment.yaml`
Add an `env` section to the container spec with `secretKeyRef` for all required secrets. Example structure:

```yaml
env:
  # Schwab API credentials
  - name: SCHWAB_CLIENT_ID
    valueFrom:
      secretKeyRef:
        name: schwab-credentials
        key: client-id
  - name: SCHWAB_CLIENT_SECRET
    valueFrom:
      secretKeyRef:
        name: schwab-credentials
        key: client-secret
  - name: SCHWAB_REDIRECT_URI
    valueFrom:
      secretKeyRef:
        name: schwab-credentials
        key: redirect-uri
  # Azure Storage
  - name: AZURE_STORAGE_CONNECTION_STRING
    valueFrom:
      secretKeyRef:
        name: azure-storage-credentials
        key: connection-string
  # Non-secret config can use configMapKeyRef or direct value
```

### Secret Naming Convention
- Group related secrets into K8s Secret objects by service (e.g. `schwab-credentials`, `azure-storage-credentials`)
- Document the required K8s Secret names in `infra/README.md` so operators know what to create before deploying

---

## Implementation Steps

1. **Audit backend env vars**: Read `backend/config.py`, `backend/services/schwab_auth.py`, `backend/services/azure_table_service.py`, `backend/services/schwab_client.py`, `backend/main.py` to enumerate all env vars
2. **Update `backend/.env.example`**: Rewrite to match actual env vars with comments
3. **Read and fix `frontend/vue-app/src/api/client.js`**: Replace incorrect env var with `import.meta.env.VITE_API_BASE_URL`
4. **Update `frontend/vue-app/.env.example`**: Ensure `VITE_API_BASE_URL` is documented
5. **Read `infra/k8s/deployment.yaml`**: Understand current structure
6. **Update `infra/k8s/deployment.yaml`**: Add `env` entries with `secretKeyRef` for all required secrets
7. **Update `infra/README.md`**: Document required K8s Secret objects and their keys
8. **Verify `tests/test_project_structure.py`**: Check if any structural tests need updating

---

## Test Strategy

- **Structural test**: `tests/test_project_structure.py` may validate env file contents — review and update if needed
- **Frontend unit tests**: Existing component tests in `frontend/vue-app/src/components/__tests__/` should still pass; verify `client.js` change doesn't break mocked API calls
- **Manual/E2E**: Deploy to K8s with the updated manifest and confirm the backend pod starts and can authenticate to Schwab and Azure Storage
- **Config validation**: Add or verify a test that `backend/config.py` can load all required env vars without error when they are set

---

## Edge Cases

- If `VITE_API_BASE_URL` is not set at build time, the frontend should fall back gracefully (e.g. relative URL or localhost) rather than crashing
- K8s secrets must exist in the cluster before the deployment is applied — document this prerequisite clearly
- Some env vars may be optional (e.g. feature flags) — mark them as optional with defaults in `.env.example`
- The `SCHWAB_REDIRECT_URI` may not be a secret — consider whether it belongs in a ConfigMap instead
- Ensure no secrets are committed to the repo (`.gitignore` already covers `.env` files, but verify)
