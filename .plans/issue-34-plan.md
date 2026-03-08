# Implementation Plan: Azure Container Registry Bicep Module

## Approach

Create a dedicated `acr.bicep` module under `infra/bicep/modules/` that provisions an Azure Container Registry. Update `main.bicep` to call this module and pass the AKS kubelet identity so a `AcrPull` role assignment can be created. No application code changes are needed — only infrastructure files.

---

## Files to Create

### `infra/bicep/modules/acr.bicep`
New Bicep module that:
- Declares parameters: `acrName`, `location`, `sku` (default `Basic`), `aksKubeletPrincipalId`
- Provisions `Microsoft.ContainerRegistry/registries` with admin user disabled (best practice; AKS uses managed identity)
- Creates a `Microsoft.Authorization/roleAssignments` scoped to the registry, granting the AKS kubelet identity the built-in `AcrPull` role (`7f951dda-4ed3-4680-a7ca-43fe172d538d`)
- Outputs: `acrName` (string), `acrLoginServer` (string)

---

## Files to Modify

### `infra/bicep/main.bicep`
- Add a parameter `acrName` (string) with a sensible default or require it explicitly
- Add a parameter `acrSku` (string, default `'Basic'`)
- Add a module block calling `./modules/acr.bicep`, passing:
  - `acrName`
  - `location`
  - `sku: acrSku`
  - `aksKubeletPrincipalId`: sourced from the AKS module output (the kubelet identity object ID)
- Expose `acrLoginServer` as an output from `main.bicep` so CI/CD pipelines can reference it

### `infra/bicep/main.bicepparam.example`
- Add example values for `acrName` and `acrSku` so operators know what to supply

---

## Implementation Steps

1. **Create `infra/bicep/modules/acr.bicep`**
   ```bicep
   @description('Name of the Azure Container Registry (must be globally unique, 5-50 alphanumeric chars)')
   param acrName string

   @description('Azure region')
   param location string

   @description('SKU for the registry')
   @allowed(['Basic', 'Standard', 'Premium'])
   param sku string = 'Basic'

   @description('Object ID of the AKS kubelet managed identity (for AcrPull role assignment)')
   param aksKubeletPrincipalId string

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

   // Built-in AcrPull role definition ID
   var acrPullRoleDefinitionId = subscriptionResourceId(
     'Microsoft.Authorization/roleDefinitions',
     '7f951dda-4ed3-4680-a7ca-43fe172d538d'
   )

   resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
     name: guid(acr.id, aksKubeletPrincipalId, acrPullRoleDefinitionId)
     scope: acr
     properties: {
       roleDefinitionId: acrPullRoleDefinitionId
       principalId: aksKubeletPrincipalId
       principalType: 'ServicePrincipal'
     }
   }

   output acrName string = acr.name
   output acrLoginServer string = acr.properties.loginServer
   ```

2. **Update `infra/bicep/main.bicep`**
   - Add parameters:
     ```bicep
     param acrName string
     @allowed(['Basic', 'Standard', 'Premium'])
     param acrSku string = 'Basic'
     ```
   - Verify the existing `aks` module outputs the kubelet identity principal ID. If not, add that output to `aks.bicep` (see step 3).
   - Add module block:
     ```bicep
     module acr './modules/acr.bicep' = {
       name: 'acrDeploy'
       params: {
         acrName: acrName
         location: location
         sku: acrSku
         aksKubeletPrincipalId: aks.outputs.kubeletPrincipalId
       }
     }
     ```
   - Add output:
     ```bicep
     output acrLoginServer string = acr.outputs.acrLoginServer
     ```

3. **Update `infra/bicep/modules/aks.bicep`** (if not already present)
   - Ensure the module outputs the kubelet identity object ID:
     ```bicep
     output kubeletPrincipalId string = aksCluster.properties.identityProfile.kubeletidentity.objectId
     ```
   - This is required for the role assignment in the ACR module.

4. **Update `infra/bicep/main.bicepparam.example`**
   - Add:
     ```
     acrName: 'myoptionsacr'   // globally unique, alphanumeric only
     acrSku: 'Basic'
     ```

---

## Test Strategy

- **Bicep lint**: Run `az bicep lint` (or `bicep build`) on `main.bicep` and `modules/acr.bicep` to catch syntax/type errors.
- **What-if deployment**: Run `az deployment group what-if` against a test resource group to validate the plan without creating resources.
- **Integration (manual/CI)**: Deploy to a non-production resource group and verify:
  - ACR resource exists with the correct name and SKU
  - Admin user is disabled
  - AKS node pool can pull a test image from the registry (confirms role assignment is effective)
- **Idempotency**: Re-run the deployment and confirm no changes are reported (role assignment GUID is deterministic via `guid()`).

---

## Edge Cases to Handle

- **ACR name uniqueness**: ACR names must be globally unique and 5–50 alphanumeric characters. Document this constraint in the param description and `.bicepparam.example`.
- **AKS identity type**: If the AKS cluster uses a system-assigned identity rather than a user-assigned kubelet identity, the `kubeletidentity` path in `identityProfile` may differ. Confirm the identity configuration in `aks.bicep`.
- **Role assignment already exists**: Bicep's `guid()` produces a deterministic name, so re-deployments are idempotent. No special handling needed.
- **SKU downgrade**: Azure does not support downgrading ACR SKU (e.g., Premium → Basic). Document that SKU changes may require resource recreation.
- **Private networking**: If the AKS cluster is in a private VNet, a `Basic` SKU ACR may not support private endpoints (requires `Premium`). Note this in comments.
