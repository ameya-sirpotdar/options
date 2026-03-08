@description('Azure region for the Static Web App')
param location string

@minLength(2)
@maxLength(40)
@description('Name of the Static Web App resource.')
param staticSiteName string

@description('Resource tags')
param tags object = {}

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticSiteName
  location: location
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {}
}

@description('Resource ID of the Static Web App')
output staticSiteId string = staticWebApp.id

@description('Default hostname of the Static Web App')
output defaultHostname string = staticWebApp.properties.defaultHostname

@description('Name of the Static Web App')
output staticSiteName string = staticWebApp.name
