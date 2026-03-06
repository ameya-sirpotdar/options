targetScope = 'subscription'

@description('Azure region for all resources')
param location string = 'eastus'

@description('Environment name used to generate resource names')
param environmentName string = 'dev'

@description('Name of the resource group to create')
param resourceGroupName string = 'rg-options-pipeline-${environmentName}'

@description('Number of AKS agent nodes')
param aksNodeCount int = 2

@description('VM size for AKS agent nodes')
param aksNodeVmSize string = 'Standard_B2s'

@description('Name of the AKS cluster')
param aksClusterName string = 'aks-options-pipeline-${environmentName}'

@description('Name of the Storage account')
param storageAccountName string = 'stoptions${environmentName}'

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

@description('Resource ID of the AKS cluster')
output aksClusterId string = aks.outputs.clusterId

@description('Name of the Storage account')
output storageAccountName string = storage.outputs.storageAccountName

@description('Primary endpoint for Azure Table Storage')
output tableStorageEndpoint string = storage.outputs.tableStorageEndpoint