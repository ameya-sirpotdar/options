targetScope = 'subscription'

@description('Azure region for all resources')
param location string = 'eastus'

@description('Environment name used to build resource names')
param environmentName string = 'dev'

@description('Name of the resource group to create')
param resourceGroupName string = 'rg-options-analyzer-${environmentName}'

@description('AKS cluster name')
param aksClusterName string = 'aks-options-analyzer-${environmentName}'

@description('Storage account name (must be globally unique, 3-24 lowercase alphanumeric)')
param storageAccountName string

@description('Number of AKS agent nodes')
param aksNodeCount int = 2

@description('VM size for AKS agent nodes')
param aksNodeVmSize string = 'Standard_B2s'

@description('Kubernetes version')
param kubernetesVersion string = '1.29'

@description('Tags to apply to all resources')
param tags object = {
  project: 'options-analyzer'
  environment: environmentName
  managedBy: 'bicep'
}

// ---------------------------------------------------------------------------
// Resource group
// ---------------------------------------------------------------------------

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ---------------------------------------------------------------------------
// AKS module
// ---------------------------------------------------------------------------

module aks 'modules/aks.bicep' = {
  name: 'deploy-aks'
  scope: rg
  params: {
    clusterName: aksClusterName
    location: location
    nodeCount: aksNodeCount
    nodeVmSize: aksNodeVmSize
    kubernetesVersion: kubernetesVersion
    tags: tags
  }
}

// ---------------------------------------------------------------------------
// Storage module
// ---------------------------------------------------------------------------

module storage 'modules/storage.bicep' = {
  name: 'deploy-storage'
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

@description('AKS cluster resource ID')
output aksClusterId string = aks.outputs.clusterId

@description('AKS cluster FQDN')
output aksClusterFqdn string = aks.outputs.clusterFqdn

@description('Storage account name')
output storageAccountName string = storage.outputs.storageAccountName

@description('Storage account primary endpoint (table)')
output storageTableEndpoint string = storage.outputs.tableEndpoint