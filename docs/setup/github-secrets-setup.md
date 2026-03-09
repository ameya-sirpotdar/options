# GitHub Secrets and Variables Setup

This document describes all required GitHub Actions secrets and variables needed to deploy the frontend via Azure Static Web Apps (SWA).

---

## Overview

The deployment pipeline performs a pre-flight validation check before attempting to deploy. If any required secret or variable is missing, the job will fail immediately with a clear error message pointing to this document.

---

## Required GitHub Secrets

Secrets are encrypted and used for sensitive values. Set these under:
**Repository → Settings → Secrets and variables → Actions → Secrets**

| Secret Name | Description | How to Obtain |
|---|---|---|
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Deployment token for Azure Static Web Apps | See [Obtaining the SWA Deployment Token](#obtaining-the-swa-deployment-token) |
| `AZURE_CLIENT_ID` | Azure service principal client ID | See [Creating a Service Principal](#creating-a-service-principal) |
| `AZURE_CLIENT_SECRET` | Azure service principal client secret | See [Creating a Service Principal](#creating-a-service-principal) |
| `AZURE_TENANT_ID` | Azure Active Directory tenant ID | See [Finding Your Tenant ID](#finding-your-tenant-id) |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | See [Finding Your Subscription ID](#finding-your-subscription-id) |

---

## Required GitHub Variables

Variables are plaintext and used for non-sensitive configuration. Set these under:
**Repository → Settings → Secrets and variables → Actions → Variables**

| Variable Name | Description | Example Value |
|---|---|---|
| `AZURE_RESOURCE_GROUP` | Name of the Azure resource group | `my-app-rg` |
| `AZURE_SWA_NAME` | Name of the Azure Static Web App resource | `my-app-swa` |
| `AZURE_LOCATION` | Azure region for the deployment | `australiaeast` |

---

## Step-by-Step Setup

### Obtaining the SWA Deployment Token

1. Log in to the [Azure Portal](https://portal.azure.com)
2. Navigate to your **Static Web App** resource
3. In the left sidebar, select **Manage deployment token** (under Settings)
4. Click **Copy** to copy the token value
5. Add it as the `AZURE_STATIC_WEB_APPS_API_TOKEN` secret in GitHub

Alternatively, using the Azure CLI:

```bash
az staticwebapp secrets list \
  --name <your-swa-name> \
  --resource-group <your-resource-group> \
  --query "properties.apiKey" \
  --output tsv
```

---

### Creating a Service Principal

A service principal allows GitHub Actions to authenticate with Azure.

```bash
az ad sp create-for-rbac \
  --name "github-actions-<your-repo-name>" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
  --sdk-auth
```

This command outputs a JSON object. Map the fields to GitHub secrets as follows:

| JSON Field | GitHub Secret |
|---|---|
| `clientId` | `AZURE_CLIENT_ID` |
| `clientSecret` | `AZURE_CLIENT_SECRET` |
| `tenantId` | `AZURE_TENANT_ID` |
| `subscriptionId` | `AZURE_SUBSCRIPTION_ID` |

> **Note:** Store the full JSON output somewhere safe. You will not be able to retrieve the `clientSecret` again after this point.

---

### Finding Your Tenant ID

```bash
az account show --query tenantId --output tsv
```

Or in the Azure Portal:
1. Navigate to **Azure Active Directory**
2. Select **Overview**
3. Copy the **Tenant ID** value

---

### Finding Your Subscription ID

```bash
az account show --query id --output tsv
```

Or in the Azure Portal:
1. Navigate to **Subscriptions**
2. Copy the **Subscription ID** for the relevant subscription

---

## Validating Your Configuration Locally

Before pushing, you can validate that your local environment has the expected configuration using the provided script:

```bash
bash scripts/validate-github-config.sh
```

This script checks that all required secrets and variables are documented and that the workflow references them correctly. See the script itself for details on what is checked.

---

## Pre-flight Check in CI

The `deploy-frontend` job in `.github/workflows/deploy.yml` runs a pre-flight step that validates all required secrets and variables are present before proceeding with the deployment.

If the pre-flight check fails, you will see output similar to:

```
❌ Missing secret: AZURE_STATIC_WEB_APPS_API_TOKEN
❌ Missing variable: AZURE_RESOURCE_GROUP

Pre-flight validation failed. 2 required configuration value(s) are missing.
Please follow the setup guide: docs/setup/github-secrets-setup.md
```

No deployment steps will run until all required values are present.

---

## Rotating Secrets

### Rotating the SWA Deployment Token

1. In the Azure Portal, navigate to your Static Web App
2. Select **Manage deployment token**
3. Click **Reset token**
4. Copy the new token
5. Update the `AZURE_STATIC_WEB_APPS_API_TOKEN` secret in GitHub

### Rotating the Service Principal Secret

```bash
az ad sp credential reset \
  --id <AZURE_CLIENT_ID> \
  --query password \
  --output tsv
```

Update the `AZURE_CLIENT_SECRET` secret in GitHub with the new value.

---

## Troubleshooting

### Pre-flight fails even though secrets are set

- Confirm the secret/variable names match **exactly** (they are case-sensitive)
- Ensure the secret is set at the **repository** level, not just at the environment level, unless your workflow targets a specific environment
- Check that the workflow has permission to read the secrets (not restricted by a branch protection rule or environment protection rule)

### `az staticwebapp secrets list` returns empty

- Confirm you are logged in to the correct Azure subscription: `az account show`
- Confirm the SWA resource name and resource group are correct
- Ensure your account has at least the **Contributor** role on the resource

### Service principal authentication fails

- Verify the tenant ID matches the directory where the service principal was created
- Check that the service principal has not expired: `az ad sp show --id <AZURE_CLIENT_ID>`
- Confirm the subscription ID is correct and the service principal has the required role assignment

### Deployment token is valid but deploy still fails

- Ensure the SWA resource in Azure matches the `AZURE_SWA_NAME` variable
- Check that the resource group name in `AZURE_RESOURCE_GROUP` is correct
- Review the full workflow logs for additional error output from the SWA deploy action

---

## References

- [Azure Static Web Apps documentation](https://learn.microsoft.com/en-us/azure/static-web-apps/)
- [GitHub Actions encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub Actions variables](https://docs.github.com/en/actions/learn-github-actions/variables)
- [Azure CLI reference — staticwebapp](https://learn.microsoft.com/en-us/cli/azure/staticwebapp)
- [Azure service principal with Azure CLI](https://learn.microsoft.com/en-us/cli/azure/create-an-azure-service-principal-azure-cli)