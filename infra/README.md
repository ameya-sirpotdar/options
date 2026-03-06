# Infrastructure

This directory contains the Azure cloud infrastructure definitions for the Options Pricing & Sentiment Analysis platform, provisioned as Infrastructure as Code (IaC) using [Azure Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview).

---

## Directory Structure

```
infra/
├── bicep/
│   ├── main.bicep                  # Subscription-scope entry point
│   ├── main.bicepparam.example     # Example parameters file (copy and fill in)
│   ├── .gitignore                  # Protects secrets and local param files
│   └── modules/
│       ├── aks.bicep               # Azure Kubernetes Service module
│       └── storage.bicep           # Azure Storage Account + Tables module
└── README.md                       # This file
```

---

## Prerequisites

Before deploying, ensure you have the following installed and configured:

| Tool | Version | Purpose |
|------|---------|---------|
| [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) | ≥ 2.50.0 | Authenticate and deploy to Azure |
| [Bicep CLI](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/install) | ≥ 0.22.0 | Compile and validate Bicep templates |
| An Azure subscription | — | Target environment for provisioned resources |

Verify your installations:

```bash
az --version
az bicep version
```

---

## Provisioned Resources

### Azure Kubernetes Service (AKS)

Defined in `bicep/modules/aks.bicep`.

| Property | Value |
|----------|-------|
| Node count | 2 |
| VM size | `Standard_B2s` |
| OS disk size | 30 GB |
| Network plugin | `kubenet` |
| DNS prefix | Derived from cluster name |

The AKS cluster is used to host the containerised microservices that perform options pricing calculations and sentiment analysis.

### Azure Storage Account

Defined in `bicep/modules/storage.bicep`.

| Property | Value |
|----------|-------|
| SKU | `Standard_LRS` |
| Kind | `StorageV2` |
| Access tier | `Hot` |
| TLS | Minimum TLS 1.2 |
| Public blob access | Disabled |

The following Azure Table Storage tables are created automatically:

| Table name | Purpose |
|------------|---------|
| `optionsdata` | Stores computed options pricing results |
| `sentimentdata` | Stores sentiment analysis results |
| `runlogs` | Stores pipeline run audit logs |

---

## Quickstart: Deploy to Azure

### 1. Log in to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Prepare your parameters file

Copy the example parameters file and fill in your values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
```

Edit `infra/bicep/main.bicepparam` with your chosen values:

```bicep
using './main.bicep'

param environmentName = 'dev'
param location        = 'uksouth'
param aksClusterName  = 'aks-options-dev'
param storageAccountName = 'stooptionsdev'
```

> **Note:** `main.bicepparam` is listed in `.gitignore` and will never be committed to source control.

### 3. Create the Resource Group

```bash
az group create \
  --name "rg-options-dev" \
  --location "uksouth"
```

### 4. Deploy the Bicep stack

Deploy at **subscription scope** (the main entry point creates the resource group and delegates to modules):

```bash
az deployment sub create \
  --location "uksouth" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

Or deploy directly to an existing resource group (resource-group scope):

```bash
az deployment group create \
  --resource-group "rg-options-dev" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### 5. Verify the deployment

```bash
az deployment sub show \
  --name main \
  --query "properties.provisioningState"
```

Expected output: `"Succeeded"`

---

## Linting and Validation

Validate the Bicep templates without deploying:

```bash
# Lint all Bicep files
az bicep lint --file infra/bicep/main.bicep

# What-if deployment (dry run)
az deployment sub what-if \
  --location "uksouth" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

---

## Environments

The templates are parameterised to support multiple deployment environments. Use a separate parameters file per environment:

| Environment | Parameters file | Resource group |
|-------------|----------------|----------------|
| Development | `main.dev.bicepparam` | `rg-options-dev` |
| Staging | `main.staging.bicepparam` | `rg-options-staging` |
| Production | `main.prod.bicepparam` | `rg-options-prod` |

All environment-specific parameter files match the pattern `*.bicepparam` (excluding `*.example`) and are excluded from version control via `.gitignore`.

---

## Security Considerations

- **Secrets are never committed.** Parameter files containing real values are excluded via `.gitignore`.
- **Public blob access is disabled** on the Storage Account.
- **Minimum TLS 1.2** is enforced on the Storage Account.
- AKS uses a **system-assigned managed identity** — no credentials need to be managed manually.
- Review and restrict network access rules before deploying to production.

---

## Teardown

To remove all provisioned resources:

```bash
az group delete \
  --name "rg-options-dev" \
  --yes \
  --no-wait
```

> **Warning:** This permanently deletes all resources and data within the resource group. Ensure any important data is backed up before running this command.

---

## Contributing

When modifying infrastructure:

1. Run `az bicep lint` on all changed files before opening a pull request.
2. Run `az deployment sub what-if` to review planned changes.
3. Update this README if new resources or modules are added.
4. Never commit real credentials, subscription IDs, or storage account keys.