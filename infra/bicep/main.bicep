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

@description('SKU for the Azure Container Registry')
param acrSku string = 'Basic'

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
    acrSku: acrSku
  }
}

// ---------------------------------------------------------------------------
// AcrPull role assignment – allows AKS kubelet identity to pull images
// ---------------------------------------------------------------------------

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.outputs.acrId, aks.outputs.kubeletIdentityObjectId, acrPullRoleDefinitionId)
  scope: resourceGroup(resourceGroupName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
    principalId: aks.outputs.kubeletIdentityObjectId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    acr
    aks
  ]
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