# Implementation Plan: CI/CD Pipeline for Infrastructure and Application Deployment

## Approach Overview

Create a single GitHub Actions workflow file (`.github/workflows/deploy.yml`) triggered on push to `main`, with three jobs gated by path filters:

1. **`deploy-infra`** — deploys `infra/bicep/main.bicep` via `az deployment sub create`
2. **`deploy-backend`** — builds and pushes Docker image to ACR, then applies K8s manifests to AKS
3. **`deploy-frontend`** — builds the Vue app and deploys to Azure Static Web App

Additionally, a new `infra/bicep/modules/acr.bicep` module must be created and wired into `infra/bicep/main.bicep` since ACR is a prerequisite for backend image deployment but is not currently provisioned.

All jobs use `azure/login` with OIDC federation (preferred) or service principal credentials stored as GitHub secrets.

---

## Files to Create

### `.github/workflows/deploy.yml`
Main CI/CD workflow. Three jobs with path-based conditions:
- `deploy-infra`: triggered when `infra/bicep/**` changes
- `deploy-backend`: triggered when `backend/**` changes
- `deploy-frontend`: triggered when `frontend/**` changes

### `infra/bicep/modules/acr.bicep`
Bicep module to provision Azure Container Registry. Parameters: `acrName`, `location`, `sku` (default: `Basic`). Outputs: `acrLoginServer`, `acrName`.

---

## Files to Modify

### `infra/bicep/main.bicep`
- Add `module acr 'modules/acr.bicep'` referencing the new ACR module
- Output `acrLoginServer` and `acrName` for use in the pipeline
- Ensure `acrName` parameter is added (or derived from a naming convention)

### `infra/k8s/deployment.yaml`
- Verify `${ACR_NAME}` and `${IMAGE_TAG}` placeholders are present (document expected format)
- No structural changes needed if placeholders already exist

---

## Implementation Steps

### Step 1: Create ACR Bicep Module

Create `infra/bicep/modules/acr.bicep`:

```bicep
@description('Name of the Azure Container Registry')
param acrName string

@description('Azure region')
param location string

@description('SKU for ACR')
@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Basic'

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
  }
}

output acrLoginServer string = acr.properties.loginServer
output acrName string = acr.name
```

### Step 2: Update `infra/bicep/main.bicep`

Add ACR module reference and parameter:

```bicep
@description('Name for the Azure Container Registry (globally unique)')
param acrName string

module acr 'modules/acr.bicep' = {
  name: 'acrDeploy'
  params: {
    acrName: acrName
    location: location
  }
}

output acrLoginServer string = acr.outputs.acrLoginServer
output acrName string = acr.outputs.acrName
```

### Step 3: Create `.github/workflows/deploy.yml`

```yaml
name: Deploy to Azure

on:
  push:
    branches:
      - main

permissions:
  id-token: write   # Required for OIDC
  contents: read

env:
  AZURE_RESOURCE_GROUP: ${{ vars.AZURE_RESOURCE_GROUP }}
  AZURE_LOCATION: ${{ vars.AZURE_LOCATION }}
  AKS_CLUSTER_NAME: ${{ vars.AKS_CLUSTER_NAME }}
  ACR_NAME: ${{ vars.ACR_NAME }}

jobs:
  # ─────────────────────────────────────────
  # Job 1: Detect changed paths
  # ─────────────────────────────────────────
  changes:
    runs-on: ubuntu-latest
    outputs:
      infra: ${{ steps.filter.outputs.infra }}
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            infra:
              - 'infra/bicep/**'
            backend:
              - 'backend/**'
            frontend:
              - 'frontend/**'

  # ─────────────────────────────────────────
  # Job 2: Deploy Infrastructure (Bicep)
  # ─────────────────────────────────────────
  deploy-infra:
    needs: changes
    if: needs.changes.outputs.infra == 'true'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Deploy Bicep
        uses: azure/arm-deploy@v2
        with:
          scope: subscription
          region: ${{ env.AZURE_LOCATION }}
          template: infra/bicep/main.bicep
          parameters: >
            acrName=${{ env.ACR_NAME }}
          deploymentName: main-${{ github.run_number }}
          failOnStdErr: false

  # ─────────────────────────────────────────
  # Job 3: Build & Deploy Backend → AKS
  # ─────────────────────────────────────────
  deploy-backend:
    needs: changes
    if: needs.changes.outputs.backend == 'true'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - name: Log in to ACR
        run: az acr login --name ${{ env.ACR_NAME }}

      - name: Set image tag
        id: tag
        run: echo "IMAGE_TAG=${{ github.sha }}" >> $GITHUB_OUTPUT

      - name: Build and push Docker image
        run: |
          IMAGE=${{ env.ACR_NAME }}.azurecr.io/backend:${{ steps.tag.outputs.IMAGE_TAG }}
          docker build -t $IMAGE ./backend
          docker push $IMAGE

      - name: Get AKS credentials
        run: |
          az aks get-credentials \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --name ${{ env.AKS_CLUSTER_NAME }} \
            --overwrite-existing

      - name: Substitute and apply K8s manifests
        env:
          IMAGE_TAG: ${{ steps.tag.outputs.IMAGE_TAG }}
        run: |
          export ACR_NAME=${{ env.ACR_NAME }}
          export IMAGE_TAG=$IMAGE_TAG
          envsubst < infra/k8s/deployment.yaml | kubectl apply -f -
          kubectl apply -f infra/k8s/service.yaml

      - name: Verify rollout
        run: kubectl rollout status deployment/backend --timeout=120s

  # ─────────────────────────────────────────
  # Job 4: Build & Deploy Frontend → SWA
  # ─────────────────────────────────────────
  deploy-frontend:
    needs: changes
    if: needs.changes.outputs.frontend == 'true'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/vue-app/package-lock.json

      - name: Install dependencies
        working-directory: frontend/vue-app
        run: npm ci

      - name: Build Vue app
        working-directory: frontend/vue-app
        run: npm run build

      - name: Deploy to Static Web App
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.SWA_DEPLOYMENT_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: upload
          app_location: frontend/vue-app
          output_location: dist
          skip_app_build: true
```

### Step 4: Document Required Secrets

Add a `## CI/CD Secrets` section to `infra/README.md` listing:

| Secret / Variable | Where Used | Description |
|---|---|---|
| `AZURE_CLIENT_ID` | All jobs | OIDC app registration client ID |
| `AZURE_TENANT_ID` | All jobs | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | All jobs | Azure subscription ID |
| `SWA_DEPLOYMENT_TOKEN` | deploy-frontend | SWA deployment token from Azure portal |
| `AZURE_RESOURCE_GROUP` (var) | deploy-backend | Resource group name |
| `AZURE_LOCATION` (var) | deploy-infra | Azure region (e.g. eastus) |
| `AKS_CLUSTER_NAME` (var) | deploy-backend | AKS cluster name |
| `ACR_NAME` (var) | deploy-backend | ACR registry name (no `.azurecr.io`) |

---

## Test Strategy

1. **Dry-run Bicep**: Use `az deployment sub what-if` in a PR check job to validate templates without deploying
2. **Docker build smoke test**: Add a `docker build` step in a PR workflow (no push) to catch Dockerfile errors early
3. **Workflow syntax**: Use `actionlint` in CI to lint workflow YAML
4. **Path filter validation**: Manually trigger with changes to each path group to confirm correct job isolation
5. **Rollout verification**: `kubectl rollout status` with timeout catches failed deployments

---

## Edge Cases to Handle

- **First-time deploy**: ACR may not exist when backend job runs if infra job hasn't run yet — document that infra must be deployed first, or add an explicit dependency
- **Concurrent runs**: Use GitHub environment protection rules to prevent concurrent production deployments
- **Frontend not yet built**: The frontend job gracefully skips if `frontend/vue-app/` has no `package.json` (only `.gitkeep` exists) — add a guard step
- **`envsubst` availability**: `envsubst` is available on `ubuntu-latest` via `gettext` package; confirm or add install step
- **AKS→ACR role assignment**: Prefer managed identity / role assignment over admin credentials; document this in README
