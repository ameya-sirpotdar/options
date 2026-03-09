# Implementation Plan: Issue #45 — Frontend Deploy Unblocked via GitHub Secrets/Variables

## Approach Overview

This issue is fundamentally an operational configuration task: the required GitHub secrets and variables must be set by a human with appropriate access. However, the implementation agent can deliver meaningful value by:

1. Creating a **setup documentation file** (`docs/setup/github-secrets-setup.md`) that provides step-by-step instructions for configuring each secret and variable.
2. Creating a **validation/pre-flight script** (`scripts/validate-github-config.sh`) that operators can run locally to verify Azure resources exist and retrieve the SWA deployment token.
3. Improving the **deploy workflow** (`.github/workflows/deploy.yml`) to add explicit, human-readable validation steps that fail fast with clear error messages when secrets/variables are missing — rather than failing deep in the deploy action with cryptic errors.
4. Updating `.env.example` files and `CLAUDE.md` to document the required configuration.

## Files to Create

### `docs/setup/github-secrets-setup.md`
Step-by-step guide for configuring all required GitHub secrets and variables. Includes:
- How to retrieve `AZURE_STATIC_WEB_APPS_API_TOKEN` via Azure CLI
- How to find `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- How to set GitHub repository secrets via CLI (`gh secret set`) and UI
- How to set GitHub repository variables via CLI (`gh variable set`) and UI
- Verification steps to confirm the pipeline will succeed

### `scripts/validate-github-config.sh`
Bash script that:
- Checks Azure CLI is authenticated
- Verifies the SWA resource exists in the expected resource group
- Retrieves and displays (masked) the SWA deployment token
- Lists the required secrets/variables and their expected values
- Provides `gh` CLI commands to set each one

## Files to Modify

### `.github/workflows/deploy.yml`
Add a `validate-secrets` job (or pre-step within `deploy-frontend`) that:
- Runs before the deploy steps
- Checks that `AZURE_STATIC_WEB_APPS_API_TOKEN` is non-empty
- Checks that `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` are non-empty
- Checks that `VITE_API_BASE_URL`, `AZURE_RESOURCE_GROUP`, `AZURE_LOCATION` variables are set
- Emits a clear, actionable error message referencing `docs/setup/github-secrets-setup.md` if any are missing
- Fails fast before attempting the OIDC login or SWA deploy

### `CLAUDE.md`
Add a section documenting the required GitHub secrets and variables so future agents and developers are aware of the configuration requirements.

## Implementation Steps

### Step 1: Create setup documentation
Create `docs/setup/github-secrets-setup.md` with:
```markdown
# GitHub Secrets & Variables Setup for CI/CD

## Required Secrets

### AZURE_STATIC_WEB_APPS_API_TOKEN
Retrieve with:
```bash
az staticwebapp secrets list --name swa-options-pipeline-dev --query "properties.apiKey" -o tsv
```
Set with:
```bash
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body "<token>"
```

### AZURE_CLIENT_ID
The client ID of the Entra ID app registration used for OIDC federated login.
```bash
gh secret set AZURE_CLIENT_ID --body "<client-id>"
```

### AZURE_TENANT_ID
```bash
az account show --query tenantId -o tsv
gh secret set AZURE_TENANT_ID --body "<tenant-id>"
```

### AZURE_SUBSCRIPTION_ID
```bash
az account show --query id -o tsv
gh secret set AZURE_SUBSCRIPTION_ID --body "<subscription-id>"
```

## Required Variables

### VITE_API_BASE_URL
Backend API base URL injected at build time. Use a placeholder until backend is live:
```bash
gh variable set VITE_API_BASE_URL --body "https://placeholder.example.com"
```

### AZURE_RESOURCE_GROUP
```bash
gh variable set AZURE_RESOURCE_GROUP --body "rg-options-pipeline-dev"
```

### AZURE_LOCATION
```bash
gh variable set AZURE_LOCATION --body "westus3"
```

## Verification
After setting all secrets and variables, trigger a manual workflow run:
```bash
gh workflow run deploy.yml
```
```

### Step 2: Create validation script
Create `scripts/validate-github-config.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SWA_NAME="swa-options-pipeline-dev"
RG="rg-options-pipeline-dev"

echo "=== Azure Static Web App Deployment Token ==="
TOKEN=$(az staticwebapp secrets list --name "$SWA_NAME" --resource-group "$RG" --query "properties.apiKey" -o tsv 2>/dev/null || echo "ERROR: Could not retrieve token")
if [[ "$TOKEN" == ERROR* ]]; then
  echo "❌ $TOKEN"
else
  echo "✅ Token retrieved (${#TOKEN} chars)"
  echo ""
  echo "Set it with:"
  echo "  gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --body \"<token>\""
fi

echo ""
echo "=== Azure Account Info ==="
TENANT=$(az account show --query tenantId -o tsv 2>/dev/null || echo "NOT_LOGGED_IN")
SUB=$(az account show --query id -o tsv 2>/dev/null || echo "NOT_LOGGED_IN")
echo "Tenant ID:       $TENANT"
echo "Subscription ID: $SUB"

echo ""
echo "=== Required GitHub Secrets ==="
for secret in AZURE_STATIC_WEB_APPS_API_TOKEN AZURE_CLIENT_ID AZURE_TENANT_ID AZURE_SUBSCRIPTION_ID; do
  STATUS=$(gh secret list --json name --jq ".[].name" 2>/dev/null | grep -x "$secret" || echo "")
  if [[ -n "$STATUS" ]]; then
    echo "✅ $secret"
  else
    echo "❌ $secret — NOT SET"
  fi
done

echo ""
echo "=== Required GitHub Variables ==="
for var in VITE_API_BASE_URL AZURE_RESOURCE_GROUP AZURE_LOCATION; do
  STATUS=$(gh variable list --json name --jq ".[].name" 2>/dev/null | grep -x "$var" || echo "")
  if [[ -n "$STATUS" ]]; then
    echo "✅ $var"
  else
    echo "❌ $var — NOT SET"
  fi
done
```

### Step 3: Improve deploy.yml with pre-flight validation
Add a validation step at the beginning of the `deploy-frontend` job (before OIDC login):

```yaml
- name: Validate required secrets and variables
  shell: bash
  env:
    SWA_TOKEN: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
    CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
    TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
    SUB_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    API_URL: ${{ vars.VITE_API_BASE_URL }}
    RESOURCE_GROUP: ${{ vars.AZURE_RESOURCE_GROUP }}
    LOCATION: ${{ vars.AZURE_LOCATION }}
  run: |
    MISSING=()
    [[ -z "$SWA_TOKEN" ]]      && MISSING+=("Secret: AZURE_STATIC_WEB_APPS_API_TOKEN")
    [[ -z "$CLIENT_ID" ]]      && MISSING+=("Secret: AZURE_CLIENT_ID")
    [[ -z "$TENANT_ID" ]]      && MISSING+=("Secret: AZURE_TENANT_ID")
    [[ -z "$SUB_ID" ]]         && MISSING+=("Secret: AZURE_SUBSCRIPTION_ID")
    [[ -z "$API_URL" ]]        && MISSING+=("Variable: VITE_API_BASE_URL")
    [[ -z "$RESOURCE_GROUP" ]] && MISSING+=("Variable: AZURE_RESOURCE_GROUP")
    [[ -z "$LOCATION" ]]       && MISSING+=("Variable: AZURE_LOCATION")
    if [[ ${#MISSING[@]} -gt 0 ]]; then
      echo "❌ Missing required GitHub configuration:"
      for item in "${MISSING[@]}"; do
        echo "   - $item"
      done
      echo ""
      echo "See docs/setup/github-secrets-setup.md for setup instructions."
      exit 1
    fi
    echo "✅ All required secrets and variables are configured."
```

### Step 4: Update CLAUDE.md
Add a section:
```markdown
## GitHub Secrets & Variables

The CI/CD pipeline requires the following to be configured in GitHub repository settings.
See `docs/setup/github-secrets-setup.md` for full setup instructions.

### Secrets
- `AZURE_STATIC_WEB_APPS_API_TOKEN` — SWA deployment token
- `AZURE_CLIENT_ID` — Entra ID app registration client ID
- `AZURE_TENANT_ID` — Azure AD tenant ID
- `AZURE_SUBSCRIPTION_ID` — Azure subscription ID

### Variables
- `VITE_API_BASE_URL` — Backend API URL (build-time injection)
- `AZURE_RESOURCE_GROUP` — `rg-options-pipeline-dev`
- `AZURE_LOCATION` — `westus3`
```

## Test Strategy

1. **Workflow validation step test**: Temporarily unset one secret in a test branch and confirm the pre-flight step fails with the correct error message.
2. **Script smoke test**: Run `scripts/validate-github-config.sh` locally with Azure CLI authenticated to confirm it correctly identifies missing/present secrets.
3. **End-to-end**: After a human sets all secrets/variables, trigger `gh workflow run deploy.yml` and confirm the `deploy-frontend` job succeeds and the app is accessible at `https://lively-plant-0fa95be0f.4.azurestaticapps.net`.

## Edge Cases

- `VITE_API_BASE_URL` may be a placeholder URL until the backend is deployed — the validation only checks it is non-empty, not that it resolves.
- The SWA resource is in `eastus2` (per the issue) but `AZURE_LOCATION` is `westus3` — this discrepancy should be noted in the docs (the location variable may refer to a different resource, e.g., AKS).
- The validation script requires both `az` CLI and `gh` CLI to be installed and authenticated.
- GitHub Actions secrets are not readable after being set (only their presence can be checked via the API); the pre-flight step correctly handles this by checking for empty string.
