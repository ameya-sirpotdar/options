# Infrastructure – Azure Cloud Resources

This directory contains the Infrastructure-as-Code (IaC) for provisioning all Azure cloud resources required by the project, implemented with [Azure Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview).

---

## Directory Structure

```
infra/
├── bicep/
│   ├── main.bicep                  # Subscription-scope entry point
│   ├── main.bicepparam.example     # Example parameters file (copy to main.bicepparam)
│   ├── .gitignore                  # Prevents committing real parameter files
│   └── modules/
│       ├── aks.bicep               # Azure Kubernetes Service cluster
│       └── storage.bicep           # Azure Storage account + tables
└── README.md                       # This file
```

---

## Resources Provisioned

### Resource Group
A dedicated resource group is created at the subscription scope to contain all project resources.

### Azure Kubernetes Service (AKS) – `modules/aks.bicep`
| Property | Value |
|---|---|
| Node count | 2 |
| Node VM size | `Standard_B2s` |
| Kubernetes version | Latest stable (resolved at deploy time) |
| Network plugin | `kubenet` |
| Identity | System-assigned managed identity |

### Azure Storage Account – `modules/storage.bicep`
| Property | Value |
|---|---|
| SKU | `Standard_LRS` |
| Kind | `StorageV2` |
| Access tier | `Hot` |
| TLS | Minimum TLS 1.2 |
| Public blob access | Disabled |

#### Storage Tables
The following Azure Storage Tables are created automatically:

| Table name | Purpose |
|---|---|
| `optionsdata` | Raw options chain data ingested from market feeds |
| `sentimentdata` | Processed sentiment scores and signals |
| `runlogs` | Pipeline execution logs and audit trail |

---

## Prerequisites

Before deploying, ensure you have the following installed and configured:

1. **Azure CLI** ≥ 2.50.0  
   ```bash
   az --version
   ```

2. **Bicep CLI** (installed automatically with a recent Azure CLI, or manually)  
   ```bash
   az bicep install
   az bicep version
   ```

3. **An active Azure subscription** with sufficient permissions:
   - `Contributor` or `Owner` at the **subscription** scope (required because `main.bicep` deploys at subscription scope to create the resource group)

4. **Logged in to Azure CLI**  
   ```bash
   az login
   az account set --subscription "<your-subscription-id>"
   ```

---

## Configuration

### 1. Create your parameters file

Copy the example parameters file and fill in your values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
```

Edit `infra/bicep/main.bicepparam` with your environment-specific values:

```bicep
using './main.bicep'

param location         = 'eastus'
param resourceGroupName = 'rg-myproject-prod'
param aksClusterName   = 'aks-myproject-prod'
param storageAccountName = 'stmyprojectprod'
param environment      = 'prod'
```

> **Important:** `main.bicepparam` is listed in `.gitignore` and must **never** be committed to source control, as it may contain environment-specific or sensitive values.

### Parameter Reference

| Parameter | Type | Description | Example |
|---|---|---|---|
| `location` | string | Azure region for all resources | `eastus` |
| `resourceGroupName` | string | Name of the resource group to create | `rg-myproject-prod` |
| `aksClusterName` | string | Name of the AKS cluster | `aks-myproject-prod` |
| `storageAccountName` | string | Globally unique storage account name (3–24 lowercase alphanumeric) | `stmyprojectprod` |
| `environment` | string | Environment tag applied to all resources (`dev`, `staging`, `prod`) | `prod` |

---

## Deployment

All commands below are run from the **repository root**.

### Deploy (create or update)

```bash
az deployment sub create \
  --name "provision-$(date +%Y%m%d%H%M%S)" \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### What-if (dry run – preview changes without deploying)

```bash
az deployment sub what-if \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### Validate (syntax and schema check only)

```bash
az deployment sub validate \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

---

## Outputs

After a successful deployment the following values are emitted as deployment outputs and can be retrieved with:

```bash
az deployment sub show \
  --name "<deployment-name>" \
  --query properties.outputs
```

| Output | Description |
|---|---|
| `aksClusterName` | Name of the provisioned AKS cluster |
| `aksResourceId` | Full Azure resource ID of the AKS cluster |
| `storageAccountName` | Name of the provisioned storage account |
| `storageAccountId` | Full Azure resource ID of the storage account |
| `resourceGroupName` | Name of the resource group that was created |

---

## Connecting to the AKS Cluster

After deployment, merge the cluster credentials into your local `kubeconfig`:

```bash
az aks get-credentials \
  --resource-group "<resourceGroupName>" \
  --name "<aksClusterName>" \
  --overwrite-existing
```

Verify connectivity:

```bash
kubectl get nodes
```

---

## Accessing Storage Tables

Retrieve the storage account connection string (for local development only – prefer managed identity in production):

```bash
az storage account show-connection-string \
  --resource-group "<resourceGroupName>" \
  --name "<storageAccountName>" \
  --query connectionString \
  --output tsv
```

List tables to confirm they were created:

```bash
az storage table list \
  --account-name "<storageAccountName>" \
  --output table
```

---

## Teardown

> **Warning:** This will permanently delete the resource group and **all resources** inside it.

```bash
az group delete \
  --name "<resourceGroupName>" \
  --yes \
  --no-wait
```

---

## CI/CD Integration

For automated deployments (e.g., GitHub Actions), store the following as repository secrets:

| Secret | Description |
|---|---|
| `AZURE_CREDENTIALS` | Service principal JSON (`az ad sp create-for-rbac --sdk-auth`) |
| `AZURE_SUBSCRIPTION_ID` | Target subscription ID |

Example GitHub Actions step:

```yaml
- name: Deploy Bicep infrastructure
  uses: azure/arm-deploy@v1
  with:
    scope: subscription
    subscriptionId: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    region: eastus
    template: infra/bicep/main.bicep
    parameters: >
      location=eastus
      resourceGroupName=rg-myproject-prod
      aksClusterName=aks-myproject-prod
      storageAccountName=stmyprojectprod
      environment=prod
```

---

## Security Notes

- Real parameter files (`*.bicepparam`, excluding `*.example`) are excluded from version control via `.gitignore`.
- The storage account is configured with `allowBlobPublicAccess: false` and minimum TLS 1.2.
- AKS uses a system-assigned managed identity; avoid using service principals with long-lived credentials where possible.
- Apply the principle of least privilege when assigning roles to the AKS managed identity and any CI/CD service principals.