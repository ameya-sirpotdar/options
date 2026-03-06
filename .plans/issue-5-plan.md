# Implementation Plan: Story 1.3 – Provision Azure Cloud Resources

## Tool Choice: Bicep vs Terraform

Before proceeding, here is an honest comparison to inform the decision. Since you have ruled out multi-cloud portability, that removes Terraform's most commonly cited advantage.

### Comparison Table

| Dimension | Bicep | Terraform |
|---|---|---|
| **Azure-nativeness** | First-party Microsoft tool; always supports new Azure features on day one | Third-party; new Azure features sometimes lag by weeks or months |
| **Learning curve** | Simpler syntax; closer to ARM JSON but far more readable | HCL is clean but adds a separate language/ecosystem to learn |
| **State management** | No state file; Azure Resource Manager is the source of truth | Requires managing a state file (local or remote); common source of operational pain |
| **Drift detection** | `what-if` shows live drift against ARM; no state to go stale | State file can drift from reality; `terraform refresh` needed |
| **Tooling & IDE support** | Official VS Code extension with IntelliSense, type checking, linting | Mature ecosystem but third-party |
| **CI/CD integration** | Native Azure DevOps tasks and GitHub Actions; `az deployment` CLI | Requires installing Terraform binary; more CI setup |
| **Modularity** | Bicep modules are well-supported and composable | Terraform modules are mature and widely shared on the registry |
| **Multi-cloud** | Azure only | AWS, GCP, Azure, and many others |
| **Community/ecosystem** | Smaller but growing; backed by Microsoft | Very large community; abundant examples |
| **Secrets/sensitive outputs** | No built-in `sensitive` flag on outputs (handled via Key Vault pattern) | `sensitive = true` on outputs suppresses terminal display |
| **Past pain points you cited** | N/A | State corruption, provider version conflicts, plan/apply drift |

### Recommendation

**Use Bicep.** Given that:

1. You are Azure-only and have no plans to change.
2. Your past Terraform experience was negative — the most common pain points (state file management, provider version drift, state corruption) are entirely absent from Bicep.
3. Bicep has no state file to manage; Azure Resource Manager itself tracks what exists.
4. Bicep is maintained by Microsoft, so AKS and Storage Table support is always current.
5. The `az deployment` CLI and `what-if` command give you safe, readable previews equivalent to `terraform plan`.

The rest of this plan uses Bicep.

---

## Approach

Use Bicep (the `/infra/` directory already exists as a placeholder) to define all Azure infrastructure as code. The plan will create modular, well-structured Bicep files covering:

- Azure Resource Group (deployed at subscription scope)
- Azure Kubernetes Service (AKS) with a 2-node `Standard_B2s` node pool
- Azure Storage Account with three tables: `optionsdata`, `sentimentdata`, `runlogs`

A `main.bicepparam.example` file will be provided so developers can supply their own values without committing secrets. Deployment is performed via the Azure CLI (`az deployment`) — no additional tooling installation required beyond the Azure CLI itself.

---

## Directory Structure

```
infra/
  bicep/
    main.bicep                  # Subscription-scope entry point; creates resource group
    main.bicepparam.example     # Example parameters file (copy to main.bicepparam)
    modules/
      aks.bicep                 # AKS cluster module
      storage.bicep             # Storage account + tables module
  README.md                     # Prerequisites, deployment instructions, variable reference
```

---

## Files to Create

### `/infra/bicep/main.bicep`
Subscription-scope deployment that creates the resource group and calls child modules for AKS and storage.

### `/infra/bicep/main.bicepparam.example`
Example Bicep parameters file. Developers copy this to `main.bicepparam` (gitignored) and fill in their values.

### `/infra/bicep/modules/aks.bicep`
Bicep module defining the `Microsoft.ContainerService/managedClusters` resource.

### `/infra/bicep/modules/storage.bicep`
Bicep module defining the `Microsoft.Storage/storageAccounts` resource and three table resources.

### `/infra/README.md`
Documentation covering prerequisites, authentication, parameter reference, and the full deployment workflow.

### `/infra/bicep/.gitignore`
Ensures `main.bicepparam` and any generated ARM JSON files are not committed.

---

## Files to Modify

### `/infra/terraform/.gitkeep` and `/infra/.gitkeep`
Remove these placeholder files once real Bicep files are added.

### `tests/test_project_structure.py`
Add assertions to verify that the expected Bicep files exist under `/infra/bicep/`.

### `/.gitignore`
Add Bicep-specific ignores.

---

## Implementation Steps

### Step 1 — Remove placeholder files
Delete `/infra/.gitkeep` and `/infra/terraform/.gitkeep`. The `/infra/terraform/` directory can be removed entirely since Bicep replaces it, or kept empty with a note if the directory is referenced elsewhere.

---

### Step 2 — Create `/infra/bicep/modules/aks.bicep`

```bicep
@description('Azure region for the AKS cluster.')
param location string

@description('Name of the AKS cluster.')
param aksClusterName string

@description('Name of the resource group (used for tagging reference only).')
param environment string

@description('Number of nodes in the default node pool.')
param nodeCount int = 2

@description('VM size for AKS nodes.')
param nodeVmSize string = 'Standard_B2s'

resource aksCluster 'Microsoft.ContainerService/managedClusters@2023-05-01' = {
  name: aksClusterName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    dnsPrefix: aksClusterName
    agentPoolProfiles: [
      {
        name: 'default'
        count: nodeCount
        vmSize: nodeVmSize
        mode: 'System'
      }
    ]
  }
  tags: {
    environment: environment
  }
}

@description('Name of the provisioned AKS cluster.')
output aksClusterName string = aksCluster.name

@description('Principal ID of the AKS system-assigned managed identity.')
output aksPrincipalId string = aksCluster.identity.principalId
```

---

### Step 3 — Create `/infra/bicep/modules/storage.bicep`

```bicep
@description('Azure region for the storage account.')
param location string

@description('Globally unique storage account name (3–24 lowercase alphanumeric characters).')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Environment label for tagging.')
param environment string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  tags: {
    environment: environment
  }
}

resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource optionsDataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  parent: tableService
  name: 'optionsdata'
}

resource sentimentDataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  parent: tableService
  name: 'sentimentdata'
}

resource runLogsTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  parent: tableService
  name: 'runlogs'
}

@description('Name of the provisioned storage account.')
output storageAccountName string = storageAccount.name

@description('Primary table storage endpoint.')
output primaryTableEndpoint string = storageAccount.properties.primaryEndpoints.table
```

---

### Step 4 — Create `/infra/bicep/main.bicep`

This file is deployed at **subscription scope** so it can create the resource group itself, eliminating the need to pre-create it manually.

```bicep
targetScope = 'subscription'

@description('Name of the Azure Resource Group. Defaults to rg-options-trading-mvp.')
param resourceGroupName string = 'rg-options-trading-mvp'

@description('Azure region in which to deploy all resources.')
param location string = 'eastus'

@description('Name of the AKS cluster.')
param aksClusterName string = 'aks-options-trading-mvp'

@description('Globally unique storage account name (3–24 lowercase alphanumeric characters).')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Number of nodes in the AKS default node pool.')
param nodeCount int = 2

@description('VM size for AKS nodes.')
param nodeVmSize string = 'Standard_B2s'

@description('Deployment environment label (e.g. dev, staging, prod).')
param environment string = 'dev'

// Create the resource group at subscription scope
resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: {
    environment: environment
  }
}

// Deploy AKS cluster into the resource group
module aks 'modules/aks.bicep' = {
  name: 'aksDeployment'
  scope: resourceGroup
  params: {
    location: location
    aksClusterName: aksClusterName
    environment: environment
    nodeCount: nodeCount
    nodeVmSize: nodeVmSize
  }
}

// Deploy storage account and tables into the resource group
module storage 'modules/storage.bicep' = {
  name: 'storageDeployment'
  scope: resourceGroup
  params: {
    location: location
    storageAccountName: storageAccountName
    environment: environment
  }
}

@description('Name of the provisioned resource group.')
output resourceGroupName string = resourceGroup.name

@description('Name of the provisioned AKS cluster.')
output aksClusterName string = aks.outputs.aksClusterName

@description('Principal ID of the AKS managed identity.')
output aksPrincipalId string = aks.outputs.aksPrincipalId

@description('Name of the provisioned storage account.')
output storageAccountName string = storage.outputs.storageAccountName

@description('Primary table storage endpoint.')
output primaryTableEndpoint string = storage.outputs.primaryTableEndpoint
```

---

### Step 5 — Create `/infra/bicep/main.bicepparam.example`

```bicep
using './main.bicep'

// Copy this file to main.bicepparam and fill in your values.
// main.bicepparam is gitignored and must never be committed.

// Name of the Azure Resource Group (default: 'rg-options-trading-mvp')
param resourceGroupName = 'rg-options-trading-mvp'

// Azure region (default: 'eastus')
param location = 'eastus'

// AKS cluster name (default: 'aks-options-trading-mvp')
param aksClusterName = 'aks-options-trading-mvp'

// Storage account name — must be globally unique, 3–24 lowercase alphanumeric chars
// Replace <unique-suffix> with something unique to your subscription, e.g. your initials + random digits
param storageAccountName = 'stoptionsmvp<unique-suffix>'

// Number of AKS nodes (default: 2)
param nodeCount = 2

// AKS node VM size (default: 'Standard_B2s')
param nodeVmSize = 'Standard_B2s'

// Environment label (default: 'dev')
param environment = 'dev'
```

---

### Step 6 — Create `/infra/bicep/.gitignore`

```gitignore
# Local parameters file — may contain sensitive values, never commit
main.bicepparam

# Compiled ARM JSON output (if using bicep build locally)
*.json
!.bicep/*.example.json
```

---

### Step 7 — Update root `/.gitignore`

Add the following section:

```gitignore
# Bicep
infra/bicep/main.bicepparam
infra/bicep/*.json
```

---

### Step 8 — Create `/infra/README.md`

````markdown
# Infrastructure – Azure Provisioning (Bicep)

All Azure resources for this project are defined as Bicep templates under `infra/bicep/`.

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) >= 2.50.0 (includes Bicep support built-in)
- An Azure subscription with sufficient quota:
  - At least 4 vCPUs available for `Standard_B2s` in your target region
  - Permissions to create resource groups, AKS clusters, and storage accounts
- Contributor role (or equivalent) on the target subscription

## Authentication

```bash
az login
az account set --subscription "<your-subscription-id>"
```

For CI/CD pipelines, use a service principal:

```bash
export AZURE_CLIENT_ID="<client-id>"
export AZURE_CLIENT_SECRET="<client-secret>"
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_SUBSCRIPTION_ID="<subscription-id>"

az login --service-principal \
  --username "$AZURE_CLIENT_ID" \
  --password "$AZURE_CLIENT_SECRET" \
  --tenant "$AZURE_TENANT_ID"
```

## Setup

Copy the example parameters file and fill in your values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
# Edit main.bicepparam — set storageAccountName to a globally unique value
```

`main.bicepparam` is gitignored and must never be committed.

## Preview Changes (equivalent to terraform plan)

```bash
az deployment sub what-if \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

The `what-if` command shows exactly what will be created, modified, or deleted — no changes are applied.

## Deploy

```bash
az deployment sub create \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam \
  --name "options-trading-mvp-$(date +%Y%m%d%H%M%S)"
```

## Destroy / Clean Up

Bicep does not have a built-in destroy command. Delete the resource group to remove all provisioned resources:

```bash
az group delete --name rg-options-trading-mvp --yes --no-wait
```

Replace `rg-options-trading-mvp` with your configured `resourceGroupName` if you used a different value.

## Input Parameters

| Parameter | Description | Default |
|---|---|---|
| `resourceGroupName` | Name of the Azure Resource Group | `rg-options-trading-mvp` |
| `location` | Azure region | `eastus` |
| `aksClusterName` | AKS cluster name | `aks-options-trading-mvp` |
| `storageAccountName` | Globally unique storage account name | *(required)* |
| `nodeCount` | AKS node count | `2` |
| `nodeVmSize` | AKS node VM size | `Standard_B2s` |
| `environment` | Environment label | `dev` |

## Outputs

| Output | Description |
|---|---|
| `resourceGroupName` | Name of the provisioned resource group |
| `aksClusterName` | Name of the provisioned AKS cluster |
| `aksPrincipalId` | Managed identity principal ID of the AKS cluster |
| `storageAccountName` | Name of the provisioned storage account |
| `primaryTableEndpoint` | Primary Azure Table Storage endpoint URL |

## Retrieve AKS Credentials

After deployment, fetch the kubeconfig:

```bash
az aks get-credentials \