// =============================================================================
// Main Bicep entry point – subscription scope
// Provisions resource group, AKS cluster, and Storage account for the project.
// =============================================================================

targetScope = 'subscription'

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Azure region for all resources.')
param location string = 'eastus'

@description('Short environment tag (dev | staging | prod).')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Project name used as a prefix for all resource names.')
@minLength(2)
@maxLength(12)
param projectName string = 'optionsai'

@description('Number of nodes in the AKS default node pool.')
@minValue(1)
@maxValue(10)
param aksNodeCount int = 2

@description('VM size for AKS nodes.')
param aksNodeVmSize string = 'Standard_B2s'

@description('Kubernetes version to deploy.')
param kubernetesVersion string = '1.29'

@description('Name of the Storage account (must be globally unique, 3-24 lowercase alphanumeric).')
@minLength(3)
@maxLength(24)
param storageAccountName string = ''

// ---------------------------------------------------------------------------
// Variables
// ---------------------------------------------------------------------------

var resourceGroupName = '${projectName}-${environment}-rg'
var resolvedStorageAccountName = empty(storageAccountName)
  ? '${projectName}${environment}sa'
  : storageAccountName

var commonTags = {
  project: projectName
  environment: environment
  managedBy: 'bicep'
}

// ---------------------------------------------------------------------------
// Resource group
// ---------------------------------------------------------------------------

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: commonTags
}

// ---------------------------------------------------------------------------
// AKS module
// ---------------------------------------------------------------------------

module aks 'modules/aks.bicep' = {
  name: 'aks-deployment'
  scope: rg
  params: {
    location: location
    environment: environment
    projectName: projectName
    nodeCount: aksNodeCount
    nodeVmSize: aksNodeVmSize
    kubernetesVersion: kubernetesVersion
    tags: commonTags
  }
}

// ---------------------------------------------------------------------------
// Storage module
// ---------------------------------------------------------------------------

module storage 'modules/storage.bicep' = {
  name: 'storage-deployment'
  scope: rg
  params: {
    location: location
    storageAccountName: resolvedStorageAccountName
    tags: commonTags
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Name of the provisioned resource group.')
output resourceGroupName string = rg.name

@description('Name of the AKS cluster.')
output aksClusterName string = aks.outputs.clusterName

@description('FQDN of the AKS API server.')
output aksApiServerFqdn string = aks.outputs.apiServerFqdn

@description('Name of the Storage account.')
output storageAccountName string = storage.outputs.storageAccountName

@description('Names of the Table Storage tables created.')
output storageTableNames array = storage.outputs.tableNames