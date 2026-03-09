targetScope = 'subscription'

@description('Azure region for all resources')
param location string = 'eastus'

@description('Environment name used to generate resource names')
param environmentName string = 'dev'

@description('Name of the resource group to create')
param resourceGroupName string = 'rg-options-pipeline-${environmentName}'

@description('Number of AKS agent nodes')
param aksNodeCount int = 1

@description('VM size for AKS agent nodes')
param aksNodeVmSize string = 'Standard_B2s'

@description('Name of the AKS cluster')
param aksClusterName string = 'aks-options-pipeline-${environmentName}'

@description('Name of the Storage account')
param storageAccountName string = 'stoptions${environmentName}'

@description('Name of the Azure Container Registry')
param acrName string = 'acroptions${environmentName}'

@description('Name of the Azure Key Vault')
param keyVaultName string = 'kv-options-${environmentName}'

@description('SKU for the Azure Container Registry')
param acrSku string = 'Basic'

@maxLength(40)
@description('Name of the Static Web App (must be globally unique, max 40 chars)')
param staticWebAppName string = 'swa-options-pipeline-${environmentName}'

@description('Azure region for the Static Web App (Free SKU: eastus2, centralus, westus2, westeurope, eastasia)')
param swaLocation string = 'eastus2'

var tags = {
  environment: environmentName
}

// ---------------------------------------------------------------------------
// Resource group
// ---------------------------------------------------------------------------

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
}

// ---------------------------------------------------------------------------
// AKS cluster module
// ---------------------------------------------------------------------------

module aks 'modules/aks.bicep' = {
  name: 'aks-deployment'
  scope: rg
  params: {
    location: location
    clusterName: aksClusterName
    nodeCount: aksNodeCount
    nodeVmSize: aksNodeVmSize
  }
}

// ---------------------------------------------------------------------------
// Azure Container Registry module
// ---------------------------------------------------------------------------

module acr 'modules/acr.bicep' = {
  name: 'acr-deployment'
  scope: rg
  params: {
    location: location
    acrName: acrName
    skuName: acrSku
  }
}

// ---------------------------------------------------------------------------
// AcrPull role assignment – allows AKS kubelet identity to pull images
// Deployed as a module (resource-group scope) to satisfy BCP139 and BCP120
// ---------------------------------------------------------------------------

module acrPullRoleAssignment 'modules/roleassignment.bicep' = {
  name: 'acr-pull-role-assignment'
  scope: rg
  params: {
    acrName: acr.outputs.acrName
    aksPrincipalId: aks.outputs.kubeletPrincipalId
  }
}

// ---------------------------------------------------------------------------
// Storage account module
// ---------------------------------------------------------------------------

module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  scope: rg
  params: {
    location: location
    storageAccountName: storageAccountName
  }
}

// ---------------------------------------------------------------------------
// Key Vault module
// ---------------------------------------------------------------------------

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault-deployment'
  scope: rg
  params: {
    location: location
    keyVaultName: keyVaultName
    tags: tags
    readerPrincipalId: aks.outputs.kubeletIdentityObjectId
  }
}

// ---------------------------------------------------------------------------
// Static Web App module
// ---------------------------------------------------------------------------

module swa 'modules/swa.bicep' = {
  name: 'swa-deployment'
  scope: rg
  params: {
    location: swaLocation
    staticSiteName: staticWebAppName
    tags: tags
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Name of the provisioned resource group')
output resourceGroupName string = rg.name

@description('Name of the AKS cluster')
output aksClusterName string = aks.outputs.clusterName

@description('Name of the Storage account')
output storageAccountName string = storage.outputs.storageAccountName

@description('Primary endpoint for Azure Table Storage')
output tableStorageEndpoint string = storage.outputs.tableServiceEndpoint

@description('Login server URL for the Azure Container Registry')
output acrLoginServer string = acr.outputs.acrLoginServer

@description('Name of the Azure Container Registry')
output acrName string = acr.outputs.acrName

@description('Default hostname of the Static Web App')
output swaDefaultHostname string = swa.outputs.defaultHostname

@description('Resource ID of the Static Web App')
output swaResourceId string = swa.outputs.staticSiteId

@description('URI of the Azure Key Vault')
output keyVaultUri string = keyvault.outputs.keyVaultUri

@description('Name of the Azure Key Vault')
output keyVaultName string = keyvault.outputs.keyVaultName
