@description('Name of the AKS cluster')
param clusterName string

@description('Azure region for the AKS cluster')
param location string

@description('Number of nodes in the default node pool')
param nodeCount int = 2

@description('VM size for the default node pool')
param nodeVmSize string = 'Standard_B2s'

@description('Kubernetes version')
param kubernetesVersion string = '1.29'

@description('Resource tags')
param tags object = {}

@description('DNS prefix for the AKS cluster')
param dnsPrefix string = clusterName

resource aksCluster 'Microsoft.ContainerService/managedClusters@2024-01-01' = {
  name: clusterName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    dnsPrefix: dnsPrefix
    enableRBAC: true
    agentPoolProfiles: [
      {
        name: 'systempool'
        count: nodeCount
        vmSize: nodeVmSize
        osType: 'Linux'
        osDiskSizeGB: 30
        mode: 'System'
        enableAutoScaling: false
        type: 'VirtualMachineScaleSets'
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      loadBalancerSku: 'standard'
    }
    autoUpgradeProfile: {
      upgradeChannel: 'patch'
    }
    oidcIssuerProfile: {
      enabled: true
    }
    securityProfile: {
      workloadIdentity: {
        enabled: true
      }
    }
  }
}

@description('The resource ID of the AKS cluster')
output clusterResourceId string = aksCluster.id

@description('The name of the AKS cluster')
output clusterName string = aksCluster.name

@description('The FQDN of the AKS cluster')
output clusterFqdn string = aksCluster.properties.fqdn

@description('The OIDC issuer URL of the AKS cluster')
output oidcIssuerUrl string = aksCluster.properties.oidcIssuerProfile.issuerURL

@description('The principal ID of the AKS cluster system-assigned identity')
output clusterPrincipalId string = aksCluster.identity.principalId