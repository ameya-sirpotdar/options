# Infrastructure

This directory contains the Azure cloud infrastructure definitions for the project, provisioned using [Bicep](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/overview).

## Directory Structure

```
infra/
├── bicep/
│   ├── main.bicep                  # Subscription-scope entry point
│   ├── main.bicepparam.example     # Example parameters file (copy and customise)
│   ├── .gitignore                  # Prevents sensitive parameter files from being committed
│   └── modules/
│       ├── aks.bicep               # Azure Kubernetes Service cluster
│       └── storage.bicep           # Azure Storage account and tables
└── README.md                       # This file
```

## Resources Provisioned

### Resource Group

A dedicated resource group is created at the subscription scope to contain all project resources.

### Azure Kubernetes Service (AKS)

- **Module:** `bicep/modules/aks.bicep`
- **Node pool:** 2 nodes, `Standard_B2s` VM size
- **Kubernetes version:** Configurable via parameter (defaults to `1.29`)
- **Identity:** System-assigned managed identity
- **Purpose:** Hosts the containerised application workloads

### Azure Storage Account

- **Module:** `bicep/modules/storage.bicep`
- **SKU:** `Standard_LRS`
- **Kind:** `StorageV2`
- **Tables provisioned:**
  - `optionsdata` – stores raw options chain data polled from the Schwab API (one entity per contract per polling run)
  - `sentimentdata` – stores computed sentiment signals
  - `runlogs` – stores pipeline run audit logs (one entity per polling cycle)
- **Purpose:** Lightweight, cost-effective persistence layer using Azure Table Storage

## Table Schemas

### `optionsdata`

Stores one entity per options contract per polling run. Keyed for efficient retrieval by symbol and time.

| Property | Type | Description |
|---|---|---|
| `PartitionKey` | `string` | Underlying symbol (e.g. `SPY`) |
| `RowKey` | `string` | `<runId>_<contractSymbol>` |
| `runId` | `string` | UUID identifying the polling cycle that produced this record |
| `symbol` | `string` | Underlying equity symbol |
| `contractSymbol` | `string` | Full OCC-style options contract symbol |
| `putCall` | `string` | `PUT` or `CALL` |
| `strikePrice` | `double` | Strike price |
| `expirationDate` | `string` | Expiration date (ISO 8601) |
| `bid` | `double` | Bid price |
| `ask` | `double` | Ask price |
| `last` | `double` | Last traded price |
| `volume` | `int32` | Contract volume |
| `openInterest` | `int32` | Open interest |
| `impliedVolatility` | `double` | Implied volatility |
| `delta` | `double` | Delta greek |
| `gamma` | `double` | Gamma greek |
| `theta` | `double` | Theta greek |
| `vega` | `double` | Vega greek |
| `rho` | `double` | Rho greek |
| `inTheMoney` | `boolean` | Whether the contract is in the money |
| `polledAt` | `string` | ISO 8601 UTC timestamp when the data was polled |
| *(+ additional fields)* | | Up to ~45 fields from the Schwab API response |

### `runlogs`

Stores one entity per polling cycle for audit and observability purposes.

| Property | Type | Description |
|---|---|---|
| `PartitionKey` | `string` | Fixed value `runlog` |
| `RowKey` | `string` | `runId` UUID |
| `runId` | `string` | UUID identifying the polling cycle |
| `startedAt` | `string` | ISO 8601 UTC timestamp when the cycle started |
| `completedAt` | `string` | ISO 8601 UTC timestamp when the cycle completed |
| `status` | `string` | `success`, `partial`, or `failure` |
| `symbolsRequested` | `int32` | Number of symbols submitted for polling |
| `symbolsSucceeded` | `int32` | Number of symbols successfully retrieved |
| `contractspersisted` | `int32` | Total number of option contract records written |
| `errorMessage` | `string` | Error detail if status is not `success`, else empty |

## Application Configuration

The backend application connects to Azure Table Storage using a connection string supplied via environment variable. See `backend/.env.example` for the full list of required variables.

| Variable | Description |
|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Connection string for the Azure Storage account (found in the Azure Portal under **Storage account → Access keys**) |

### Retrieving the connection string after deployment

```bash
az storage account show-connection-string \
  --resource-group "<your-resource-group-name>" \
  --name "<your-storage-account-name>" \
  --query connectionString \
  --output tsv
```

Copy the output and set it as `AZURE_STORAGE_CONNECTION_STRING` in your `.env` file (never commit this value to source control).

## Prerequisites

1. [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated:
   ```bash
   az login
   az account set --subscription "<your-subscription-id>"
   ```
2. [Bicep CLI](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/install) installed (or use the version bundled with Azure CLI ≥ 2.20):
   ```bash
   az bicep install
   az bicep version
   ```

## Deployment

### 1. Create your parameters file

Copy the example parameters file and fill in your own values:

```bash
cp infra/bicep/main.bicepparam.example infra/bicep/main.bicepparam
```

Edit `infra/bicep/main.bicepparam` and set at minimum:

| Parameter | Description |
|---|---|
| `location` | Azure region (e.g. `uksouth`, `eastus`) |
| `resourceGroupName` | Name for the resource group to create |
| `aksClusterName` | Name for the AKS cluster |
| `storageAccountName` | Globally unique storage account name (3–24 lowercase alphanumeric) |
| `kubernetesVersion` | Kubernetes version (e.g. `1.29`) |

> **Note:** `main.bicepparam` is listed in `.gitignore` and will not be committed to source control. Never commit real parameter values or secrets.

### 2. Deploy at subscription scope

```bash
az deployment sub create \
  --location "<your-azure-region>" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

For example, deploying to UK South:

```bash
az deployment sub create \
  --location uksouth \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

### 3. Verify the deployment

```bash
# List resources in the new resource group
az resource list --resource-group "<your-resource-group-name>" --output table

# Check AKS cluster status
az aks show --resource-group "<your-resource-group-name>" --name "<your-aks-cluster-name>" --query provisioningState

# Check storage account tables
az storage table list --account-name "<your-storage-account-name>" --output table

# Verify optionsdata table exists
az storage table exists --account-name "<your-storage-account-name>" --name optionsdata

# Verify runlogs table exists
az storage table exists --account-name "<your-storage-account-name>" --name runlogs
```

## Tearing Down

To remove all provisioned resources, delete the resource group:

```bash
az group delete --name "<your-resource-group-name>" --yes --no-wait
```

> **Warning:** This permanently deletes all resources and data within the resource group. Ensure you have backed up any data you need before proceeding.

## Linting and Validation

Validate the Bicep templates without deploying:

```bash
# Lint all Bicep files
az bicep lint --file infra/bicep/main.bicep

# Validate the deployment (requires a parameters file)
az deployment sub validate \
  --location "<your-azure-region>" \
  --template-file infra/bicep/main.bicep \
  --parameters infra/bicep/main.bicepparam
```

## Notes

- The deployment is scoped to the **subscription level** (`targetScope = 'subscription'` in `main.bicep`). This allows Bicep to create the resource group as part of the deployment rather than requiring it to exist beforehand.
- All child modules are scoped to the resource group created by `main.bicep`.
- Storage uses **Azure Table Storage** (not Blob or Queue) for its schema-flexible, low-cost characteristics suitable for time-series financial data.
- AKS uses a **system-assigned managed identity** to avoid the need to manage service principal credentials manually.
- The `optionsdata` table is written via batch upsert in chunks of 100 entities (the Azure Table Storage maximum per batch transaction). This keeps write latency low even for large options chains.
- The `runlogs` table is written as a single entity at the end of each polling cycle and serves as the primary observability record for monitoring and alerting.
- Storage failures during a polling cycle are caught and logged as warnings; they do not crash the polling loop, ensuring the application remains resilient to transient storage errors.