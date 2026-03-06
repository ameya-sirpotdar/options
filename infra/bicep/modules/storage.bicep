targetScope = 'resourceGroup'

@description('Azure region for the Storage account')
param location string

@description('Name of the Storage account')
param storageAccountName string

@description('Tags to apply to all resources')
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
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

resource tableService 'Microsoft.Storage/storageAccounts/tableServices@2023-01-01' = {
  name: 'default'
  parent: storageAccount
  properties: {}
}

resource optionsDataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  name: 'optionsdata'
  parent: tableService
  properties: {}
}

resource sentimentDataTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  name: 'sentimentdata'
  parent: tableService
  properties: {}
}

resource runLogsTable 'Microsoft.Storage/storageAccounts/tableServices/tables@2023-01-01' = {
  name: 'runlogs'
  parent: tableService
  properties: {}
}

@description('Resource ID of the Storage account')
output storageAccountId string = storageAccount.id

@description('Name of the Storage account')
output storageAccountName string = storageAccount.name

@description('Primary endpoint for Table storage')
output tableEndpoint string = storageAccount.properties.primaryEndpoints.table