targetScope = 'subscription'

@description('Azure region for all resources')
param location string = 'eastus'

@description('Environment name used to generate resource names')
param environmentName string = 'dev'

@description('Name of the resource group to create')
param resourceGroupName string = 'rg-options-analyzer-${environmentName}'

@description('Kubernetes version for the AKS cluster')
param kubernetesVersion string = '1.29'

@description('Number of nodes in the AKS default node pool')
param aksNodeCount int = 2

@description('VM size for AKS nodes')
param aksNodeVmSize string = 'Standard_B2s'

@description('Name of the AKS cluster')
param aksClusterName string = 'aks-options-analyzer-${environmentName}'

@description('Name of the Storage Account')
param storageAccountName string = 'stooptionsanalyzer${environmentName}'

// ---------------------------------------------------------------------------
// Resource Group
// ---------------------------------------------------------------------------

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: {
    environment: environmentName
    project: 'options-analyzer'
    managedBy: 'bicep'
  }
}

// ---------------------------------------------------------------------------
// AKS Module
// ---------------------------------------------------------------------------

module aks 'modules/aks.bicep' = {
  name: 'aks-deployment'
  scope: rg
  params: {
    location: location
    clusterName: aksClusterName
    kubernetesVersion: kubernetesVersion
    nodeCount: aksNodeCount
    nodeVmSize: aksNodeVmSize
    environmentName: environmentName
  }
}

// ---------------------------------------------------------------------------
// Storage Module
// ---------------------------------------------------------------------------

module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  scope: rg
  params: {
    location: location
    storageAccountName: storageAccountName
    environmentName: environmentName
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Name of the provisioned resource group')
output resourceGroupName string = rg.name

@description('Name of the AKS cluster')
output aksClusterName string = aks.outputs.clusterName

@description('FQDN of the AKS API server')
output aksControlPlaneFqdn string = aks.outputs.controlPlaneFqdn

@description('Name of the Storage Account')
output storageAccountName string = storage.outputs.storageAccountName

@description('Primary endpoint for Azure Table Storage')
output tableStorageEndpoint string = storage.outputs.tableStorageEndpoint