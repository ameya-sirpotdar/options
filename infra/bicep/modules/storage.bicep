param location string
param storageAccountName string
param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
}

resource optionsDataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  name: 'optionsdata'
  parent: tableService
}

resource sentimentDataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  name: 'sentimentdata'
  parent: tableService
}

resource runLogsTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  name: 'runlogs'
  parent: tableService
}

output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output primaryEndpoints object = storageAccount.properties.primaryEndpoints