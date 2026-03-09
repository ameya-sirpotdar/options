# Implementation Plan: CI/CD Pipeline for Infrastructure and Application Deployment

## Approach Overview

Create a single GitHub Actions workflow file (`.github/workflows/deploy.yml`) triggered on push to `main`, with three jobs gated by path filters:

1. **`deploy-infra`** — deploys `infra/bicep/main.bicep` via `az deployment sub create`
2. **`deploy-backend`** — builds and pushes Docker image to ACR, then applies K8s manifests to AKS
3. **`deploy-frontend`** — builds the Vue app and deploys to Azure Static Web App

Additionally, a new `infra/bicep/modules/acr.bicep` module must be created and wired into `infra/bicep/main.bicep` since ACR is a prerequisite for backend image deployment but is not currently provisioned.

All jobs use `azure/login` with OIDC federation (preferred) or service principal credentials stored as GitHub secrets.

> **Blocking dependencies:** This plan is blocked by #31 (SWA infrastructure — required for frontend deployment target) and #34 (ACR infrastructure — required for backend image registry). The ACR Bicep module created here provisions ACR as part of the pipeline, but the SWA deployment token and AKS role assignments must be confirmed resolved in those issues before this pipeline is production-ready.

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

### `infra/README.md`
- Add `## CI/CD Secrets` section documenting all required secrets and variables
- Add `## First-Time Bootstrap` section documenting manual steps required before the pipeline can run

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

> **Note on admin credentials:** `adminUserEnabled` is set to `false`. The AKS cluster must be granted the `AcrPull` role on this registry via a managed identity role assignment. See the AKS→ACR Role Assignment section below and the README documentation in Step 5.

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

      - name: Install envsubst
        run: |
          # envsubst ships with gettext; confirm availability or install
          if ! command -v envsubst &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y gettext
          fi

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

      - name: Check frontend app exists
        id: frontend-check
        run: |
          if [ ! -f frontend/vue-app/package.json ]; then
            echo "skip=true" >> $GITHUB_OUTPUT
            echo "::warning::frontend/vue-app/package.json not found — skipping frontend deployment"
          else
            echo "skip=false" >> $GITHUB_OUTPUT
          fi

      - name: Setup Node.js
        if: steps.frontend-check.outputs.skip != 'true'
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/vue-app/package-lock.json

      - name: Install dependencies
        if: steps.frontend-check.outputs.skip != 'true'
        working-directory: frontend/vue-app
        run: npm ci

      - name: Build Vue app
        if: steps.frontend-check.outputs.skip != 'true'
        working-directory: frontend/vue-app
        run: npm run build

      - name: Deploy to Static Web App
        if: steps.frontend-check.outputs.skip != 'true'
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.SWA_DEPLOYMENT_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: upload
          app_location: frontend/vue-app
          output_location: dist
          skip_app_build: true
```

### Step 4: Document Required Secrets and Bootstrap Steps in `infra/README.md`

#### `## CI/CD Secrets`

Add the following table:

| Secret / Variable | Type | Where Used | Description |
|---|---|---|---|
| `AZURE_CLIENT_ID` | Secret | All jobs | OIDC app registration client ID |
| `AZURE_TENANT_ID` | Secret | All jobs | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Secret | All jobs | Azure subscription ID |
| `SWA_DEPLOYMENT_TOKEN` | Secret | `deploy-frontend` | SWA deployment token from Azure portal (available after #31 is resolved) |
| `AZURE_RESOURCE_GROUP` | Variable | `deploy-backend` | Resource group name |
| `AZURE_LOCATION` | Variable | `deploy-infra` | Azure region (e.g. `eastus`) |
| `AKS_CLUSTER_NAME` | Variable | `deploy-backend` | AKS cluster name |
| `ACR_NAME` | Variable | `deploy-backend`, `deploy-infra` | ACR registry name (without `.azurecr.io`) |

Secrets are set under **Settings → Secrets and variables → Actions** in the GitHub repository. Variables (`vars.*`) are set under the **Variables** tab in the same location.

#### `## First-Time Bootstrap`

Add the following section to document manual prerequisites that must be completed before the pipeline can run end-to-end:

1. **Deploy infrastructure manually on first run.** The `deploy-backend` job assumes ACR already exists. On the very first deployment, trigger `deploy-infra` first (e.g. by making a trivial change to `infra/bicep/`) before merging any backend changes, or run the Bicep deployment manually:
   ```bash
   az deployment sub create \
     --location eastus \
     --template-file infra/bicep/main.bicep \
     --parameters acrName=<your-acr-name>
   ```

2. **Grant AKS the `AcrPull` role on ACR.** Because `adminUserEnabled` is `false`, the AKS kubelet managed identity must be assigned the `AcrPull` role on the ACR resource. Run once after ACR and AKS are provisioned:
   ```bash
   ACR_ID=$(az acr show --name <ACR_NAME> --query id -o tsv)
   AKS_KUBELET_ID=$(az aks show \
     --resource-group <RESOURCE_GROUP> \
     --name <AKS_CLUSTER_NAME> \
     --query identityProfile.kubeletidentity.objectId -o tsv)
   az role assignment create \
     --assignee $AKS_KUBELET_ID \
     --role AcrPull \
     --scope $ACR_ID
   ```
   > This step should be automated in a future iteration by adding a role assignment resource to `infra/bicep/main.bicep`. It is documented here as a manual step until that work is scheduled.

3. **Configure OIDC federation.** The app registration identified by `AZURE_CLIENT_ID` must have a federated credential configured for the `main` branch of this repository. See [Microsoft docs on OIDC with GitHub Actions](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure).

4. **Retrieve the SWA deployment token.** After #31 provisions the Static Web App, retrieve the deployment token from the Azure portal or via:
   ```bash
   az staticwebapp secrets list --name <SWA_NAME> --query properties.apiKey -o tsv
   ```
   Store this value as the `SWA_DEPLOYMENT_TOKEN` secret.

5. **Enable GitHub environment protection rules.** Configure the `production` environment under **Settings → Environments** with required reviewers and a deployment branch policy restricted to `main`. This prevents concurrent production deployments.

---

## Test Strategy

1. **Dry-run Bicep (PR check):** Add a separate PR workflow (not included in this plan's scope but recommended as a follow-up) that runs `az deployment sub what-if` to validate Bicep templates without deploying.
2. **Docker build smoke test (PR check):** Add a `docker build` step in a PR workflow (no push) to catch Dockerfile errors before merge.
3. **Workflow syntax validation:** Use `actionlint` in CI to lint workflow YAML. Run locally with:
   ```bash
   actionlint .github/workflows/deploy.yml
   ```
4. **Path filter validation:** Manually trigger the workflow with changes scoped to each path group (`infra/bicep/`, `backend/`, `frontend/`) and confirm only the expected job runs.
5. **Rollout verification:** `kubectl rollout status deployment/backend --timeout=120s` catches failed deployments and fails the job, preventing silent rollout failures.
6. **Frontend guard validation:** Confirm the `deploy-frontend` job emits a warning and exits cleanly when `frontend/vue-app/package.json` does not exist (e.g. only `.gitkeep` is present).

---

## Edge Cases to Handle

| Edge Case | Mitigation |
|---|---|
| **First-time deploy — ACR doesn't exist** | Document in README bootstrap steps that `deploy-infra` must run before `deploy-backend`. Infra and backend changes should not be merged in the same PR on first setup. |
| **Concurrent production deployments** | GitHub environment protection rules on the `production` environment prevent concurrent runs. Document this in README. |
| **Frontend not yet scaffolded** | The `Check frontend app exists` step in `deploy-frontend`