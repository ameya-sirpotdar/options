targetScope = 'resourceGroup'

param acrName string
param aksPrincipalId string

@description('Role definition ID (GUID only, not full resource ID). See https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles for reference.')
// AcrPull built-in role — verify with: az role definition list --name AcrPull --query '[].name'
param roleDefinitionId string = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: acrName
}

var roleAssignmentName = guid(acr.id, aksPrincipalId, roleDefinitionId)

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: roleAssignmentName
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: aksPrincipalId
    principalType: 'ServicePrincipal'
  }
}
