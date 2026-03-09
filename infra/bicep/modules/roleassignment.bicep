param acrId string
param kubeletPrincipalId string
param acrPullRoleDefinitionId string = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrId, kubeletPrincipalId, acrPullRoleDefinitionId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleDefinitionId)
    principalId: kubeletPrincipalId
    principalType: 'ServicePrincipal'
  }
}
