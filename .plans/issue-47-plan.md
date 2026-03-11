# Implementation Plan: Fix Bicep Role Assignment Errors

## Approach Overview

The root causes are:
1. **BCP120** — The `name` property of the role assignment uses `acr.outputs.*` and `aks.outputs.*`, which are runtime values not known at deployment start. Bicep requires role assignment names to be deterministic at compile time (or use `guid()` with only compile-time-known values).
2. **BCP139** — A `Microsoft.Authorization/roleAssignments` resource at subscription scope must be deployed via a module scoped to the target resource group, not inline in a subscription-scoped Bicep file.
3. **Warnings** — Unnecessary `dependsOn` for `acr` and `aks` on the role assignment resource (lines 97–98) should be removed once the module approach is adopted.

### Solution
- Create a new module `infra/bicep/modules/roleassignment.bicep` scoped to `resourceGroup()` that accepts the ACR resource ID and AKS principal ID as parameters and creates the role assignment.
- In `main.bicep`, replace the inline role assignment resource with a call to this new module, passing the required parameters as outputs from the `acr` and `aks` modules.
- Use `guid(acrResourceId, aksPrincipalId, roleDefinitionId)` for the role assignment name — this is deterministic given the inputs and acceptable for Bicep.
- Remove the now-unnecessary `dependsOn` block.

## Files to Create

### `infra/bicep/modules/roleassignment.bicep`
A resource-group-scoped module that:
- Accepts parameters: `acrName` (or `acrResourceId`), `aksPrincipalId`, `roleDefinitionId`
- Creates the `Microsoft.Authorization/roleAssignments` resource with a `guid()`-based name
- Is scoped to `resourceGroup()` (default for a module, matching where ACR lives)

## Files to Modify

### `infra/bicep/main.bicep`
- Remove the inline `Microsoft.Authorization/roleAssignments` resource (lines ~89–98)
- Add a module block calling `modules/roleassignment.bicep`, passing:
  - `acrResourceId`: `acr.outputs.acrId` (or equivalent output)
  - `aksPrincipalId`: `aks.outputs.kubeletPrincipalId` (or equivalent output)
  - `roleDefinitionId`: the AcrPull role definition ID
- Ensure the module has an explicit `dependsOn: [acr, aks]` if needed (or rely on implicit dependency via parameter references)

## Implementation Steps

1. **Read `infra/bicep/main.bicep`** to understand the exact current role assignment block (lines 89–98), the module output names for ACR and AKS, and the subscription-level scope declaration.

2. **Read `infra/bicep/modules/acr.bicep`** to confirm the output name for the ACR resource ID (e.g., `acrId`, `resourceId`).

3. **Read `infra/bicep/modules/aks.bicep`** to confirm the output name for the AKS kubelet/managed identity principal ID (e.g., `kubeletPrincipalId`, `principalId`).

4. **Create `infra/bicep/modules/roleassignment.bicep`**:
```bicep
// Scoped to resource group (default) — satisfies BCP139
targetScope = 'resourceGroup'

@description('Resource ID of the Azure Container Registry')
param acrResourceId string

@description('Principal ID of the AKS kubelet managed identity')
param aksPrincipalId string

@description('Role definition ID for AcrPull')
param roleDefinitionId string = '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull built-in role

var roleAssignmentName = guid(acrResourceId, aksPrincipalId, roleDefinitionId)

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: roleAssignmentName
  scope: /* reference to ACR resource via resourceId */ 
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: aksPrincipalId
    principalType: 'ServicePrincipal'
  }
}
```

   Note: The scope must reference the ACR resource. Since we're in a resource-group module, we can use an `existing` resource reference:
```bicep
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: acrName  // pass acrName as a param instead of/in addition to acrResourceId
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, aksPrincipalId, roleDefinitionId)
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: aksPrincipalId
    principalType: 'ServicePrincipal'
  }
}
```

5. **Modify `infra/bicep/main.bicep`**:
   - Remove the inline role assignment resource block (lines ~89–98)
   - Add a module reference:
```bicep
module acrAksPull 'modules/roleassignment.bicep' = {
  name: 'acrAksPullRoleAssignment'
  scope: resourceGroup(resourceGroupName)  // or the RG where ACR is deployed
  params: {
    acrName: acr.outputs.acrName
    aksPrincipalId: aks.outputs.kubeletPrincipalId
  }
}
```
   - Implicit dependency on `acr` and `aks` is established via parameter references, so no explicit `dependsOn` needed.

6. **Verify ACR and AKS modules expose needed outputs** — if `acrName` or `kubeletPrincipalId` outputs don't exist, add them to the respective module files.

7. **Validate locally** (if Bicep CLI available): `az bicep build --file infra/bicep/main.bicep`

## Test Strategy

- **Bicep build validation**: Run `az bicep build --file infra/bicep/main.bicep` — should produce no BCP120/BCP139 errors.
- **What-if deployment**: Run `az deployment sub what-if` against a test subscription to confirm the role assignment would be created correctly.
- **CI pipeline**: Push the fix branch and confirm the "Deploy Infrastructure" job passes validation.

## Edge Cases to Handle

- If `acr.bicep` doesn't currently output `acrName`, add the output.
- If `aks.bicep` doesn't currently output the kubelet principal ID, add the output.
- The `guid()` function in the module uses `acr.id` (runtime), which is fine inside a resource-group-scoped module — BCP120 only applies at subscription scope.
- Ensure the role definition ID for AcrPull (`7f951dda-4ed3-4680-a7ca-43fe172d538d`) matches what was previously used.
- The resource group scope for the module must match where ACR is deployed — confirm this from `main.bicep`'s existing module calls.
