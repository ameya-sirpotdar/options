# Implementation Plan: Azure Static Web App Bicep Infrastructure (Issue #31)

## Approach

Add Azure Static Web App (SWA) hosting infrastructure to the existing Bicep IaC setup. This involves:
1. Creating a new `swa.bicep` module following the established pattern of `storage.bicep` and `aks.bicep`
2. Updating `main.bicep` to include the new module, parameters, and outputs

No linked repository or API proxying will be configured — deployment tokens will be handled in a separate story.

---

## Files to Create

### `infra/bicep/modules/swa.bicep`

New Bicep module that provisions an Azure Static Web App resource.

```bicep
@description('Azure region for the Static Web App.')
param location string

@description('Name of the Static Web App resource.')
param staticSiteName string

@description('Resource tags.')
param tags object = {}

resource staticSite 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticSiteName
  location: location
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    // No repositoryUrl or branch — deployment via SWA CLI / GitHub Action token
    buildProperties: {
      skipGithubActionWorkflowGeneration: true
    }
  }
}

@description('Resource ID of the Static Web App.')
output staticSiteId string = staticSite.id

@description('Default hostname of the Static Web App.')
output defaultHostname string = staticSite.properties.defaultHostname

@description('Name of the Static Web App.')
output staticSiteName string = staticSite.name
```

---

## Files to Modify

### `infra/bicep/main.bicep`

**Changes:**

1. **Add parameters** near the top of the file (after existing params):
   ```bicep
   @description('Name of the Azure Static Web App.')
   param staticWebAppName string = 'swa-options-pipeline-${environmentName}'

   @description('Azure region for the Static Web App (Free tier has limited region availability).')
   param swaLocation string = 'eastus2'
   ```

2. **Add SWA module block** after the storage module block:
   ```bicep
   module swa 'modules/swa.bicep' = {
     name: 'swa'
     scope: rg
     params: {
       location: swaLocation
       staticSiteName: staticWebAppName
       tags: tags
     }
   }
   ```

3. **Add outputs** at the bottom of the file:
   ```bicep
   @description('Default hostname of the deployed Static Web App.')
   output swaDefaultHostname string = swa.outputs.defaultHostname

   @description('Resource ID of the Static Web App.')
   output swaResourceId string = swa.outputs.staticSiteId
   ```

---

## Implementation Steps

1. **Create `infra/bicep/modules/swa.bicep`** with the resource definition, parameters, and outputs as specified above.
2. **Edit `infra/bicep/main.bicep`**:
   a. Add `staticWebAppName` and `swaLocation` parameters.
   b. Add the `swa` module block after the storage module.
   c. Add `swaDefaultHostname` and `swaResourceId` outputs.
3. **Validate both files** compile without errors:
   ```bash
   az bicep build --file infra/bicep/modules/swa.bicep
   az bicep build --file infra/bicep/main.bicep
   ```
4. **(Optional)** Update `infra/bicep/main.bicepparam.example` to document the new parameters if that file contains parameter examples.

---

## Test Strategy

- **Bicep lint/build:** Run `az bicep build` on both files to confirm no syntax or schema errors.
- **What-if deployment (optional):** Run `az deployment sub what-if` against a dev subscription to confirm the SWA resource would be created as expected without actually provisioning it.
- **Output verification:** Confirm that `swaDefaultHostname` and `swaResourceId` are present in the deployment outputs after a test deployment.

---

## Edge Cases to Handle

- **Region availability:** SWA Free tier is not available in all regions. The `swaLocation` parameter defaults to `eastus2` (supported) and is separate from the main `location` param to avoid accidental override.
- **Name uniqueness:** Static Web App names must be globally unique within Azure. The default name pattern `swa-options-pipeline-${environmentName}` should be sufficiently unique for most environments, but teams should be aware they may need to customise it.
- **SKU constraints:** Free tier limits (100 GB bandwidth, 0.5 GB storage) are acceptable for MVP. If the project grows, the SKU can be upgraded to Standard.
- **No linked repo:** `skipGithubActionWorkflowGeneration: true` prevents Azure from auto-generating a GitHub Actions workflow, which is the correct behaviour since deployment is handled separately.
