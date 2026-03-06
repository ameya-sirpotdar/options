# Infrastructure – Azure Cloud Resources

This directory contains the Infrastructure-as-Code (IaC) templates used to provision all Azure cloud resources required by the project. Resources are defined using [Azure Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview), Microsoft's domain-specific language for declarative Azure deployments.

---

## Directory Structure

```
infra/
├── bicep/
│   ├── main.bicep                  # Subscription-scope entry point
│   ├── main.bicepparam.example     # Example parameters file (safe to commit)
│   ├── .gitignore                  # Protects sensitive parameter files
│   └── modules/
│       ├── aks.bicep               # Azure Kubernetes Service cluster
│       └── storage.bicep           # Azure Storage account + tables
└── README.md                       # This file
```

---

## Resources Provisioned

### Resource Group

A dedicated resource group is created at the subscription scope to contain all project resources. The name and location are controlled via parameters.

### Azure Kubernetes Service (AKS)

| Property | Value |
|---|---|
| Node count | 2 |
| VM size | `Standard_B2s` |
| Node pool name | `systempool` |
| Identity type | System-assigned managed identity |
| DNS prefix | Derived from cluster name parameter |

The AKS cluster is suitable for development and staging workloads. For production use, review node sizing, autoscaling settings, and network policy configuration.

### Azure Storage Account

| Property | Value |
|---|---|
| SKU | `Standard_LRS` |
| Kind | `StorageV2` |
| Access tier | Hot |
| TLS | Minimum TLS 1.2 enforced |
| Public blob access | Disabled |

#### Tables Created

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
   az --version   # Requires 2.50.0 or later
   ```

2. **Bicep CLI** – Installed automatically with Azure CLI, or manually:

   ```bash
   az bicep install
   az bicep version   # Requires 0.22.0 or later
   ```

3. **Azure subscription** – You must have `Contributor` or `Owner` role at the subscription scope to create resource groups and resources.

4. **Authenticated session**:

   ```bash
   az login
   az account set --subscription "<your-subscription-id>"
   ```

---

## Configuration

### Create a Parameters File

Copy the example parameters file and fill in your values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
```

Edit `infra/bicep/main.bicepparam` with your environment-specific values:

```bicep
using './main.bicep'

param location = 'eastus'
param resourceGroupName = 'rg-myproject-dev'
param aksClusterName = 'aks-myproject-dev'
param storageAccountName = 'stmyprojectdev001'
```

> **Important:** `main.bicepparam` is listed in `.gitignore` and must never be committed to source control. It may contain sensitive or environment-specific values.

### Parameter Reference

| Parameter | Type | Description | Example |
|---|---|---|---|
| `location` | string | Azure region for all resources | `eastus` |
| `resourceGroupName` | string | Name of the resource group to create | `rg-myproject-dev` |
| `aksClusterName` | string | Name of the AKS cluster | `aks-myproject-dev` |
| `storageAccountName` | string | Globally unique storage account name (3–24 lowercase alphanumeric) | `stmyprojectdev001` |

---

## Deployment

All commands below should be run from the **repository root**.

### 1. Validate the Templates (Dry Run)

Perform a what-if analysis to preview changes before applying them:

```bash
az deployment sub what-if \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### 2. Deploy to Azure

```bash
az deployment sub create \
  --location eastus \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam \
  --name "deploy-$(date +%Y%m%d%H%M%S)"
```

The `--location` flag specifies where the deployment metadata is stored (not necessarily where resources are created – that is controlled by the `location` parameter inside the file).

### 3. Verify Deployment

Check that the resource group and resources were created:

```bash
# List resources in the new resource group
az resource list \
  --resource-group rg-myproject-dev \
  --output table

# Get AKS credentials
az aks get-credentials \
  --resource-group rg-myproject-dev \
  --name aks-myproject-dev

kubectl get nodes

# Verify storage tables
az storage table list \
  --account-name stmyprojectdev001 \
  --auth-mode login \
  --output table
```

---

## Tearing Down Resources

To delete all provisioned resources, delete the resource group:

```bash
az group delete \
  --name rg-myproject-dev \
  --yes \
  --no-wait
```

> **Warning:** This is irreversible. All data stored in the storage account will be permanently deleted.

---

## CI/CD Integration

For automated deployments from a pipeline (GitHub Actions, Azure DevOps, etc.), use a service principal or workload identity federation instead of interactive login.

### GitHub Actions Example (OIDC / Workload Identity)

```yaml
- name: Azure Login
  uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

- name: Deploy Bicep
  uses: azure/arm-deploy@v2
  with:
    scope: subscription
    region: eastus
    template: infra/bicep/main.bicep
    parameters: >
      location=eastus
      resourceGroupName=rg-myproject-prod
      aksClusterName=aks-myproject-prod
      storageAccountName=stmyprojectprod001
    deploymentName: deploy-${{ github.run_number }}
```

Store all sensitive values as [GitHub Actions secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets) and never hard-code them in workflow files.

---

## Security Considerations

- **Managed Identity**: The AKS cluster uses a system-assigned managed identity, eliminating the need to manage service principal credentials manually.
- **TLS Enforcement**: The storage account enforces a minimum of TLS 1.2 for all connections.
- **Public Blob Access Disabled**: Anonymous public access to blob containers is disabled on the storage account.
- **Parameter Files**: Real parameter files (`.bicepparam`) are excluded from version control via `.gitignore`. Only the `.example` file is committed.
- **RBAC**: Assign the principle of least privilege when granting access to the AKS cluster and storage account.

---

## Troubleshooting

### `InvalidTemplateDeployment` – Storage account name conflict

Storage account names must be globally unique across all of Azure. If you receive a conflict error, choose a different value for `storageAccountName`.

### `AuthorizationFailed` – Insufficient permissions

Ensure your account has the `Contributor` or `Owner` role at the **subscription** scope (not just the resource group), as `main.bicep` deploys at subscription scope to create the resource group.

```bash
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --output table
```

### Bicep version mismatch

If you encounter syntax errors, update the Bicep CLI:

```bash
az bicep upgrade
```

---

## Related Documentation

- [Azure Bicep documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [AKS documentation](https://learn.microsoft.com/en-us/azure/aks/)
- [Azure Table Storage documentation](https://learn.microsoft.com/en-us/azure/storage/tables/)
- [Azure CLI reference](https://learn.microsoft.com/en-us/cli/azure/)