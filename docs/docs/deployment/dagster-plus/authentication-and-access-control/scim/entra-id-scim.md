---
title: 'Configuring Microsoft Entra ID SCIM provisioning'
sidebar_position: 8320
sidebar_label: 'Microsoft Entra ID (formerly Azure Active Directory)'
description: Configure Microsoft Entra ID provisioning for Dagster+ to sync user information between Microsoft Entra ID and your Dagster+ deployment.
tags: [dagster-plus-feature]
---

In this guide, we'll walk you through configuring [Microsoft Entra ID provisioning](https://learn.microsoft.com/en-us/entra/architecture/sync-scim) for Dagster+.

## Prerequisites

To complete the steps in this guide, you'll need:

- **To have set up Entra ID SSO for Dagster+.** For more information, see the [Entra ID setup guide](/deployment/dagster-plus/authentication-and-access-control/sso/azure-ad-sso).
- **Permissions in Entra ID that allow you to configure SSO and SCIM provisioning.**
- **The following in Dagster+:**
  - A Pro plan
  - [Organization Admin permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) in your organization

## Steps

Follow the steps in the [Microsoft Dagster Cloud provisioning tutorial](https://learn.microsoft.com/en-us/azure/active-directory/saas-apps/dagster-cloud-provisioning-tutorial).

Once Entra ID successfully syncs users to Dagster+, synced users will have a 'synced' icon next to them in the Dagster+ users page:

![Synced/external user icon next to user in Dagster+ user list](/images/dagster-plus/features/authentication-and-access-control/dagster-cloud-external-user.png)

User groups synced from Entra ID will appear on the Dagster+ teams page:

![](/images/dagster-plus/features/authentication-and-access-control/azure/entra-id-teams-in-dagster-plus.png)

## Next steps

For more information on how user and team management works when SCIM provisioning is enabled, see the [main page of this section](/deployment/dagster-plus/authentication-and-access-control/scim).
