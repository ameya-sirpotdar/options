# Infrastructure – Azure Provisioning

This directory contains the Infrastructure as Code (IaC) for provisioning all Azure cloud resources required by the project. Resources are defined using [Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview), Microsoft's domain-specific language for Azure Resource Manager (ARM) templates.

---

## Directory Structure

```
infra/
├── bicep/
│   ├── main.bicep                  # Subscription-scoped entry point; creates resource group and calls modules
│   ├── main.bicepparam.example     # Safe example parameter file (commit-safe, no secrets)
│   ├── .gitignore                  # Protects real .bicepparam files from accidental commits
│   └── modules/
│       ├── aks.bicep               # Azure Kubernetes Service cluster definition
│       └── storage.bicep           # Azure Storage account and Table Storage definition
└── README.md                       # This file
```

---

## Resources Provisioned

### Resource Group
A dedicated Azure Resource Group is created at the subscription scope to contain all project resources.

### Azure Kubernetes Service (AKS) – `modules/aks.bicep`
| Property | Value |
|---|---|
| Node count | 2 |
| Node VM size | `Standard_B2s` |
| Kubernetes version | Latest stable (resolved at deploy time) |
| Network plugin | `kubenet` |
| Identity type | `SystemAssigned` |

### Azure Storage Account – `modules/storage.bicep`
| Property | Value |
|---|---|
| SKU | `Standard_LRS` |
| Kind | `StorageV2` |
| Access tier | `Hot` |
| TLS minimum version | `TLS1_2` |
| HTTPS only | `true` |

#### Table Storage Tables
The following tables are created within the Storage Account:

| Table Name | Purpose |
|---|---|
| `optionsdata` | Stores raw and processed options chain data |
| `sentimentdata` | Stores sentiment analysis results |
| `runlogs` | Stores pipeline execution logs and audit records |

---

## Prerequisites

Before deploying, ensure you have the following installed and configured:

1. **Azure CLI** – [Install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
   ```bash
   az --version   # Verify installation
   ```

2. **Bicep CLI** – Installed automatically with a recent Azure CLI, or manually:
   ```bash
   az bicep install
   az bicep version   # Verify installation
   ```

3. **Azure Subscription** – You must have an active Azure subscription and sufficient permissions to:
   - Create Resource Groups (requires `Contributor` or `Owner` at subscription scope)
   - Create AKS clusters
   - Create Storage Accounts

4. **Authenticated Azure CLI session**:
   ```bash
   az login
   az account set --subscription "<your-subscription-id>"
   ```

---

## Configuration

### Parameter File

A safe example parameter file is provided at `infra/bicep/main.bicepparam.example`. Copy it and fill in your values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
```

Then edit `infra/bicep/main.bicepparam` with your environment-specific values:

```bicep
using './main.bicep'

param location = 'eastus'
param resourceGroupName = 'rg-your-project-name'
param aksClusterName = 'aks-your-project-name'
param storageAccountName = 'styourprojectname'
```

> **Important:** The real `main.bicepparam` file is listed in `infra/bicep/.gitignore` and must **never** be committed to source control. It may contain sensitive or environment-specific values.

### Parameter Reference

| Parameter | Type | Description | Example |
|---|---|---|---|
| `location` | `string` | Azure region for all resources | `eastus` |
| `resourceGroupName` | `string` | Name of the resource group to create | `rg-myproject-prod` |
| `aksClusterName` | `string` | Name of the AKS cluster | `aks-myproject-prod` |
| `storageAccountName` | `string` | Globally unique storage account name (3–24 lowercase alphanumeric) | `stmyprojectprod` |

---

## Deployment

### Full Deployment (Recommended)

Deploy everything from the repository root using a single command. The deployment targets **subscription scope** so that the resource group can be created as part of the deployment:

```bash
az deployment sub create \
  --name "project-infra-deployment" \
  --location "eastus" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### What-If (Dry Run)

Preview all changes before applying them:

```bash
az deployment sub what-if \
  --name "project-infra-deployment" \
  --location "eastus" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### Validate Only

Validate the template and parameters without deploying:

```bash
az deployment sub validate \
  --name "project-infra-deployment" \
  --location "eastus" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

---

## Post-Deployment

### Connect to AKS

After a successful deployment, configure `kubectl` to connect to the new cluster:

```bash
az aks get-credentials \
  --resource-group "<resourceGroupName>" \
  --name "<aksClusterName>"

kubectl get nodes   # Verify connectivity; expect 2 nodes in Ready state
```

### Retrieve Storage Account Connection String

```bash
az storage account show-connection-string \
  --resource-group "<resourceGroupName>" \
  --name "<storageAccountName>" \
  --query connectionString \
  --output tsv
```

Store this connection string securely (e.g., in Azure Key Vault or as a Kubernetes Secret) for use by application workloads.

### Verify Tables Exist

```bash
az storage table list \
  --account-name "<storageAccountName>" \
  --output table
```

Expected output includes: `optionsdata`, `sentimentdata`, `runlogs`.

---

## Teardown

To remove all provisioned resources, delete the resource group:

```bash
az group delete \
  --name "<resourceGroupName>" \
  --yes \
  --no-wait
```

> **Warning:** This permanently deletes all resources within the resource group, including the AKS cluster and all data in Table Storage. This action cannot be undone.

---

## Notes

- All Bicep modules are **idempotent**: re-running the deployment will update existing resources to match the template rather than creating duplicates.
- The AKS cluster uses a `SystemAssigned` managed identity, eliminating the need to manage service principal credentials.
- Storage account names must be **globally unique** across all of Azure. If deployment fails with a name conflict, choose a different value for `storageAccountName`.
- The `Standard_B2s` VM size is cost-optimised for development and staging workloads. For production, consider upgrading to a burstable or dedicated compute tier.