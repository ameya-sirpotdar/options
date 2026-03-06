# Implementation Plan: Story 1.3 – Provision Azure Cloud Resources

## Approach

Use Terraform (the `/infra/terraform/` directory already exists as a placeholder) to define all Azure infrastructure as code. The plan will create modular, well-structured Terraform configuration files covering:
- Azure Resource Group
- Azure Kubernetes Service (AKS) with a 2-node `Standard_B2s` node pool
- Azure Storage Account with three tables: `optionsdata`, `sentimentdata`, `runlogs`

A `terraform.tfvars.example` file will be provided so developers can supply their own values without committing secrets. A CI-friendly variable structure will be used throughout.

---

## Files to Create

### `/infra/terraform/main.tf`
Root Terraform configuration. Declares the `azurerm` provider and calls child modules (or defines resources directly for simplicity at MVP scale).

### `/infra/terraform/variables.tf`
Input variable declarations: `resource_group_name`, `location`, `aks_cluster_name`, `storage_account_name`, `node_count`, `node_vm_size`, `environment`, etc.

### `/infra/terraform/outputs.tf`
Output values: AKS cluster name, kubeconfig, storage account name, storage account connection string (marked sensitive).

### `/infra/terraform/resource_group.tf`
Defines the `azurerm_resource_group` resource.

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
Example variable values file. Developers copy this to `terraform.tfvars` (gitignored) and fill in their values.

### `/infra/terraform/.terraform.lock.hcl` (generated)
Will be generated on `terraform init` — should be committed to version control per Terraform best practices.

### `/infra/README.md`
Documentation covering prerequisites, how to initialise, plan, and apply the Terraform configuration, and how to destroy resources.

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

2. **Create `variables.tf`** — Define all input variables with sensible defaults where appropriate (e.g., `location = "eastus"`, `node_count = 2`, `node_vm_size = "Standard_B2s"`).

3. **Create `resource_group.tf`** — Define `azurerm_resource_group` using the `resource_group_name` and `location` variables.

4. **Create `aks.tf`** — Define `azurerm_kubernetes_cluster`:
   ```hcl
   resource "azurerm_kubernetes_cluster" "main" {
     name                = var.aks_cluster_name
     location            = azurerm_resource_group.main.location
     resource_group_name = azurerm_resource_group.main.name
     dns_prefix          = var.aks_cluster_name

     default_node_pool {
       name       = "default"
       node_count = 2
       vm_size    = "Standard_B2s"
     }

     identity {
       type = "SystemAssigned"
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
   }

   provider "azurerm" {
     features {}
   }
   ```

7. **Create `outputs.tf`** — Expose useful outputs for downstream use (kubeconfig, storage connection string marked sensitive).

8. **Create `terraform.tfvars.example`** — Provide a template with placeholder values and comments.

9. **Create `/infra/README.md`** — Document prerequisites (Azure CLI, Terraform >= 1.3, Azure subscription), authentication steps, and `terraform init / plan / apply` workflow.

10. **Update `.gitignore`** — Ensure sensitive and generated Terraform files are excluded.

11. **Update `tests/test_project_structure.py`** — Add checks for the presence of key Terraform files.

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
- Run `terraform plan` against a real Azure subscription and verify the plan shows creation of: 1 resource group, 1 AKS cluster, 1 storage account, 3 storage tables.
- Run `terraform apply` and verify resources exist in the Azure portal.
- Run `terraform destroy` to clean up after validation.

---

## Edge Cases to Handle

- **Storage account name uniqueness**: Azure storage account names must be globally unique and 3–24 lowercase alphanumeric characters. Document this constraint and use a variable with a note.
- **AKS node pool quota**: `Standard_B2s` requires available vCPU quota in the target region. Document this as a prerequisite.
- **Terraform state**: For MVP, local state is acceptable, but add a comment in `main.tf` with a placeholder for a remote backend (Azure Blob Storage) for future use.
- **Azure provider authentication**: Document that `az login` or service principal environment variables (`ARM_CLIENT_ID`, etc.) must be set before running Terraform.
- **Region availability**: Not all VM sizes are available in all regions. Default to `eastus` which has broad availability.
