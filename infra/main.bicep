// EXAMPLE ONLY. Deploying creates billable resources; explicit owner approval required.
targetScope = 'resourceGroup'
param location string = resourceGroup().location
param workspaceName string
param tags object = { purpose: 'independent-portfolio' }

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: 30 }
}

output logWorkspaceId string = logs.id
