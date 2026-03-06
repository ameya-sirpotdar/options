targetScope = 'subscription'

@description('Azure region for all resources')
param location string = 'eastus'

@description('Environment name used to generate unique resource names')
param environmentName string

@description('Name of the resource group to create')
param resourceGroupName string = 'rg-${environmentName}'

@description('AKS cluster name')
param aksClusterName string = 'aks-${environmentName}'

@description('Number of nodes in the AKS default node pool')
param aksNodeCount int = 2

@description('VM size for AKS nodes')
param aksNodeVmSize string = 'Standard_B2s'

@description('Storage account name (must be globally unique, 3-24 lowercase alphanumeric)')
param storageAccountName string

@description('Tags to apply to all resources')
param tags object = {
  environment: environmentName
  managedBy: 'bicep'
  project: 'azure-sentiment-pipeline'
}

// ---------------------------------------------------------------------------
// Resource Group
// ---------------------------------------------------------------------------

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ---------------------------------------------------------------------------
// AKS Module
// ---------------------------------------------------------------------------

module aks 'modules/aks.bicep' = {
  name: 'aks-deployment'
  scope: rg
  params: {
    clusterName: aksClusterName
    location: location
    nodeCount: aksNodeCount
    nodeVmSize: aksNodeVmSize
    tags: tags
  }
}

// ---------------------------------------------------------------------------
// Storage Module
// ---------------------------------------------------------------------------

module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  scope: rg
  params: {
    storageAccountName: storageAccountName
    location: location
    tags: tags
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Name of the provisioned resource group')
output resourceGroupName string = rg.name

@description('AKS cluster name')
output aksClusterName string = aks.outputs.clusterName

@description('AKS cluster resource ID')
output aksClusterResourceId string = aks.outputs.clusterResourceId

@description('Storage account name')
output storageAccountName string = storage.outputs.storageAccountName

@description('Storage account resource ID')
output storageAccountResourceId string = storage.outputs.storageAccountResourceId

@description('Names of the Table Storage tables created')
output storageTableNames array = storage.outputs.tableNames