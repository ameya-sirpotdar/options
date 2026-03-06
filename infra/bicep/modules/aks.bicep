param location string
param clusterName string
param nodeCount int = 2
param nodeVmSize string = 'Standard_B2s'
param kubernetesVersion string = '1.29'
param tags object = {}

resource aksCluster 'Microsoft.ContainerService/managedClusters@2024-02-01' = {
  name: clusterName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    dnsPrefix: clusterName
    enableRBAC: true
    agentPoolProfiles: [
      {
        name: 'systempool'
        count: nodeCount
        vmSize: nodeVmSize
        osType: 'Linux'
        mode: 'System'
        enableAutoScaling: false
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      loadBalancerSku: 'standard'
    }
    addonProfiles: {
      azurePolicy: {
        enabled: true
      }
      omsAgent: {
        enabled: false
      }
    }
  }
}

output clusterName string = aksCluster.name
output clusterResourceId string = aksCluster.id
output kubeletIdentityObjectId string = aksCluster.properties.identityProfile.kubeletidentity.objectId