# Implementation Plan: Story 1.3 – Provision Azure Cloud Resources

## Approach

Use Terraform (the `/infra/terraform/` directory already exists as a placeholder) to define all Azure infrastructure as code. The plan will create modular, well-structured Terraform configuration files covering:
- Azure Resource Group
- Azure Kubernetes Service (AKS) with a 2-node `Standard_B2s` node pool
- Azure Storage Account with three tables: `optionsdata`, `sentimentdata`, `runlogs`

The resource group name will be supplied via the `resource_group_name` input variable, with a default value of `"rg-options-trading-mvp"`. This follows the Azure naming convention `rg-<workload>-<environment>` and is overridable per environment.

A `terraform.tfvars.example` file will be provided so developers can supply their own values without committing secrets. A CI-friendly variable structure will be used throughout.

---

## Files to Create

### `/infra/terraform/main.tf`
Root Terraform configuration. Declares the `azurerm` provider and calls child modules (or defines resources directly for simplicity at MVP scale).

### `/infra/terraform/variables.tf`
Input variable declarations: `resource_group_name`, `location`, `aks_cluster_name`, `storage_account_name`, `node_count`, `node_vm_size`, `environment`, etc.

The `resource_group_name` variable will be declared as:
```hcl
variable "resource_group_name" {
  description = "Name of the Azure Resource Group. Must be unique within the subscription. Defaults to 'rg-options-trading-mvp'."
  type        = string
  default     = "rg-options-trading-mvp"
}
```

### `/infra/terraform/outputs.tf`
Output values: AKS cluster name, kubeconfig, storage account name, storage account connection string (marked sensitive), and resource group name.

### `/infra/terraform/resource_group.tf`
Defines the `azurerm_resource_group` resource using `var.resource_group_name`.

### `/infra/terraform/aks.tf`
Defines the `azurerm_kubernetes_cluster` resource with:
- `default_node_pool` using `Standard_B2s` VM size
- `node_count = 2`
- System-assigned managed identity

### `/infra/terraform/storage.tf`
Defines:
- `azurerm_storage_account` resource
- Three `azurerm_storage_table` resources: `optionsdata`, `sentimentdata`, `runlogs`

### `/infra/terraform/terraform.tfvars.example`
Example variable values file. Developers copy this to `terraform.tfvars` (gitignored) and fill in their values. Includes an explicit example for `resource_group_name`.

### `/infra/terraform/.terraform.lock.hcl` (generated)
Will be generated on `terraform init` — should be committed to version control per Terraform best practices.

### `/infra/README.md`
Documentation covering prerequisites, how to initialise, plan, and apply the Terraform configuration, how to destroy resources, and a table of all input variables including `resource_group_name`.

### `/.gitignore` additions (or `/infra/terraform/.gitignore`)
Ensure `terraform.tfvars`, `*.tfstate`, `*.tfstate.backup`, and `.terraform/` directory are gitignored.

---

## Files to Modify

### `/infra/terraform/.gitkeep`
Remove this placeholder file once real Terraform files are added.

### `/infra/.gitkeep`
Remove this placeholder file once `infra/README.md` is added.

### `tests/test_project_structure.py`
Add assertions to verify that the expected Terraform files exist under `/infra/terraform/`.

---

## Implementation Steps

1. **Remove placeholder files** — Delete `/infra/.gitkeep` and `/infra/terraform/.gitkeep` as they will be replaced by real content.

2. **Create `variables.tf`** — Define all input variables with sensible defaults where appropriate:
   ```hcl
   variable "resource_group_name" {
     description = "Name of the Azure Resource Group. Must be unique within the subscription."
     type        = string
     default     = "rg-options-trading-mvp"
   }

   variable "location" {
     description = "Azure region in which to deploy all resources."
     type        = string
     default     = "eastus"
   }

   variable "aks_cluster_name" {
     description = "Name of the AKS cluster."
     type        = string
     default     = "aks-options-trading-mvp"
   }

   variable "storage_account_name" {
     description = "Globally unique storage account name (3–24 lowercase alphanumeric characters)."
     type        = string
   }

   variable "node_count" {
     description = "Number of nodes in the AKS default node pool."
     type        = number
     default     = 2
   }

   variable "node_vm_size" {
     description = "VM size for AKS nodes."
     type        = string
     default     = "Standard_B2s"
   }

   variable "environment" {
     description = "Deployment environment label (e.g. dev, staging, prod)."
     type        = string
     default     = "dev"
   }
   ```

3. **Create `resource_group.tf`** — Define `azurerm_resource_group` using the `resource_group_name` and `location` variables:
   ```hcl
   resource "azurerm_resource_group" "main" {
     name     = var.resource_group_name
     location = var.location

     tags = {
       environment = var.environment
     }
   }
   ```

4. **Create `aks.tf`** — Define `azurerm_kubernetes_cluster`:
   ```hcl
   resource "azurerm_kubernetes_cluster" "main" {
     name                = var.aks_cluster_name
     location            = azurerm_resource_group.main.location
     resource_group_name = azurerm_resource_group.main.name
     dns_prefix          = var.aks_cluster_name

     default_node_pool {
       name       = "default"
       node_count = var.node_count
       vm_size    = var.node_vm_size
     }

     identity {
       type = "SystemAssigned"
     }

     tags = {
       environment = var.environment
     }
   }
   ```

5. **Create `storage.tf`** — Define storage account and three tables:
   ```hcl
   resource "azurerm_storage_account" "main" {
     name                     = var.storage_account_name
     resource_group_name      = azurerm_resource_group.main.name
     location                 = azurerm_resource_group.main.location
     account_tier             = "Standard"
     account_replication_type = "LRS"

     tags = {
       environment = var.environment
     }
   }

   resource "azurerm_storage_table" "optionsdata" {
     name                 = "optionsdata"
     storage_account_name = azurerm_storage_account.main.name
   }

   resource "azurerm_storage_table" "sentimentdata" {
     name                 = "sentimentdata"
     storage_account_name = azurerm_storage_account.main.name
   }

   resource "azurerm_storage_table" "runlogs" {
     name                 = "runlogs"
     storage_account_name = azurerm_storage_account.main.name
   }
   ```

6. **Create `main.tf`** — Declare the `azurerm` provider with version constraints:
   ```hcl
   terraform {
     required_version = ">= 1.3.0"
     required_providers {
       azurerm = {
         source  = "hashicorp/azurerm"
         version = "~> 3.0"
       }
     }

     # TODO: Configure a remote backend for non-local environments, e.g.:
     # backend "azurerm" {
     #   resource_group_name  = "rg-tfstate"
     #   storage_account_name = "<tfstate-storage-account>"
     #   container_name       = "tfstate"
     #   key                  = "options-trading.tfstate"
     # }
   }

   provider "azurerm" {
     features {}
   }
   ```

7. **Create `outputs.tf`** — Expose useful outputs including the resource group name:
   ```hcl
   output "resource_group_name" {
     description = "Name of the provisioned Azure Resource Group."
     value       = azurerm_resource_group.main.name
   }

   output "aks_cluster_name" {
     description = "Name of the provisioned AKS cluster."
     value       = azurerm_kubernetes_cluster.main.name
   }

   output "kubeconfig" {
     description = "Raw kubeconfig for the AKS cluster."
     value       = azurerm_kubernetes_cluster.main.kube_config_raw
     sensitive   = true
   }

   output "storage_account_name" {
     description = "Name of the provisioned Storage Account."
     value       = azurerm_storage_account.main.name
   }

   output "storage_account_connection_string" {
     description = "Primary connection string for the Storage Account."
     value       = azurerm_storage_account.main.primary_connection_string
     sensitive   = true
   }
   ```

8. **Create `terraform.tfvars.example`** — Provide a template with placeholder values and comments:
   ```hcl
   # Copy this file to terraform.tfvars and fill in your values.
   # terraform.tfvars is gitignored and must never be committed.

   # Name of the Azure Resource Group (default: "rg-options-trading-mvp")
   resource_group_name = "rg-options-trading-mvp"

   # Azure region (default: "eastus")
   location = "eastus"

   # AKS cluster name (default: "aks-options-trading-mvp")
   aks_cluster_name = "aks-options-trading-mvp"

   # Storage account name — must be globally unique, 3–24 lowercase alphanumeric chars
   storage_account_name = "stoptionsmvp<unique-suffix>"

   # Number of AKS nodes (default: 2)
   node_count = 2

   # AKS node VM size (default: "Standard_B2s")
   node_vm_size = "Standard_B2s"

   # Environment label (default: "dev")
   environment = "dev"
   ```

9. **Create `/infra/README.md`** — Document prerequisites, authentication, variable reference (including `resource_group_name`), and the `terraform init / plan / apply / destroy` workflow. Include a variables table:

   | Variable | Description | Default |
   |---|---|---|
   | `resource_group_name` | Name of the Azure Resource Group | `rg-options-trading-mvp` |
   | `location` | Azure region | `eastus` |
   | `aks_cluster_name` | AKS cluster name | `aks-options-trading-mvp` |
   | `storage_account_name` | Globally unique storage account name | *(required)* |
   | `node_count` | AKS node count | `2` |
   | `node_vm_size` | AKS node VM size | `Standard_B2s` |
   | `environment` | Environment label | `dev` |

10. **Update `.gitignore`** — Ensure sensitive and generated Terraform files are excluded:
    ```
    # Terraform
    infra/terraform/terraform.tfvars
    infra/terraform/*.tfstate
    infra/terraform/*.tfstate.backup
    infra/terraform/.terraform/
    ```

11. **Update `tests/test_project_structure.py`** — Add checks for the presence of key Terraform files and the README.

---

## Test Strategy

### Structural Tests (automated, no Azure credentials needed)
- Extend `tests/test_project_structure.py` to assert that `infra/terraform/main.tf`, `variables.tf`, `outputs.tf`, `aks.tf`, `storage.tf`, and `resource_group.tf` all exist.
- Assert that `infra/README.md` exists.
- Assert that `terraform.tfvars` is NOT committed (gitignore check).

### Terraform Validation (CI-safe, no Azure credentials needed)
- Run `terraform fmt -check` to enforce formatting.
- Run `terraform validate` after `terraform init -backend=false` to catch syntax and schema errors without requiring real credentials.

### Manual / Integration Tests (requires Azure subscription)
- Run `terraform plan` against a real Azure subscription and verify the plan shows creation of: 1 resource group named `rg-options-trading-mvp` (or the configured override), 1 AKS cluster, 1 storage account, 3 storage tables.
- Run `terraform apply` and verify resources exist in the Azure portal, including the resource group `rg-options-trading-mvp`.
- Run `terraform destroy` to clean up after validation.

---

## Edge Cases to Handle

- **Resource group name uniqueness**: The default `rg-options-trading-mvp` is descriptive and follows Azure naming conventions. If deploying multiple environments to the same subscription, override `resource_group_name` (e.g. `rg-options-trading-staging`) via `terraform.tfvars` or CI environment variables.
- **Storage account name uniqueness**: Azure storage account names must be globally unique and 3–24 lowercase alphanumeric characters. Document this constraint and use a variable with a note. No default is provided to force an explicit, unique value.
- **AKS node pool quota**: `Standard_B2s` requires available vCPU quota in the target region. Document this as a prerequisite.
- **Terraform state**: For MVP, local state is acceptable, but a commented-out remote backend block is included in `main.tf` as a placeholder for future use with Azure Blob Storage.
- **Azure provider authentication**: Document that `az login` or service principal environment variables (`ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`) must be set before running Terraform.
- **Region availability**: Not all VM sizes are available in all regions. Default to `eastus` which has broad availability.