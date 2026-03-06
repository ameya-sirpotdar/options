# Infrastructure – Azure Provisioning

This directory contains the Azure infrastructure-as-code (IaC) for the project,
written in [Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview).

---

## Directory layout

```
infra/
├── bicep/
│   ├── main.bicep                  # Subscription-scope entry point
│   ├── main.bicepparam.example     # Example parameters file (safe to commit)
│   ├── .gitignore                  # Prevents real *.bicepparam files being committed
│   └── modules/
│       ├── aks.bicep               # AKS cluster module
│       └── storage.bicep           # Storage account + tables module
└── README.md                       # This file
```

---

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Azure CLI | 2.57 | <https://learn.microsoft.com/cli/azure/install-azure-cli> |
| Bicep CLI | 0.26 | `az bicep install` |
| Contributor role | – | Required on the target subscription |

Verify your tools:

```bash
az version
az bicep version
```

---

## Quick start

### 1. Log in to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### 2. Create your parameters file

Copy the example file and fill in your own values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
```

Edit `infra/bicep/main.bicepparam` and replace every placeholder value
(anything that looks like `<…>`).

> **Important** – `main.bicepparam` is listed in `.gitignore` and must
> **never** be committed to source control because it may contain secrets.

### 3. Validate the deployment (what-if)

Run a what-if check to preview the changes without applying them:

```bash
az deployment sub what-if \
  --location "uksouth" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### 4. Deploy

```bash
az deployment sub create \
  --location "uksouth" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam \
  --name "options-intelligence-$(date +%Y%m%d%H%M%S)"
```

The command will block until the deployment completes and then print a JSON
summary of all created resources.

---

## Resources provisioned

### Resource group

A single resource group is created at the subscription scope. Its name and
location are controlled by the `resourceGroupName` and `location` parameters.

### AKS cluster (`modules/aks.bicep`)

| Property | Value |
|----------|-------|
| Node pool SKU | `Standard_B2s` |
| Node count | 2 |
| Kubernetes version | latest stable (resolved by Azure) |
| Network plugin | `kubenet` |
| RBAC | Enabled |

After deployment, fetch credentials with:

```bash
az aks get-credentials \
  --resource-group "<resourceGroupName>" \
  --name "<aksClusterName>"
```

### Storage account (`modules/storage.bicep`)

| Property | Value |
|----------|-------|
| SKU | `Standard_LRS` |
| Kind | `StorageV2` |
| Access tier | `Hot` |
| Public blob access | Disabled |

Three Azure Table Storage tables are created automatically:

| Table name | Purpose |
|------------|---------|
| `optionsdata` | Raw options chain snapshots |
| `sentimentdata` | Processed sentiment scores |
| `runlogs` | Pipeline run audit log |

---

## Parameters reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `location` | string | Azure region for all resources (e.g. `uksouth`) |
| `resourceGroupName` | string | Name of the resource group to create |
| `aksClusterName` | string | Name of the AKS cluster |
| `storageAccountName` | string | Globally unique storage account name (3–24 lowercase alphanumeric) |

See `main.bicepparam.example` for a fully annotated example.

---

## Tearing down

To delete **all** provisioned resources, delete the resource group:

```bash
az group delete --name "<resourceGroupName>" --yes --no-wait
```

> This is irreversible. All data stored in Table Storage will be permanently
> deleted.

---

## CI / CD notes

- The deployment runs at **subscription scope** (`az deployment sub create`),
  so the service principal used in CI must have the **Contributor** role at the
  subscription level (or a custom role with `Microsoft.Resources/deployments/*`
  and the specific resource provider actions required).
- Store the service principal credentials as encrypted repository secrets;
  never hard-code them in Bicep files or parameter files.
- Use the `--what-if` flag in pull-request pipelines and `--confirm-with-what-if`
  for gated production deployments.