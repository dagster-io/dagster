---
title: 'Managing agent tokens in Dagster+'
sidebar_position: 200
---

:::note

This guide is applicable to Dagster+.

:::

In this guide, we'll walk you through creating and revoking agent tokens in Dagster+.

## Managing agent tokens
:::note

To manage agent tokens, you need to be an [Organization Admin](/dagster-plus/features/authentication-and-access-control/rbac/user-roles-permissions#user-permissions-reference) in Dagster+.

:::

Agent tokens are used to authenticate [Hybrid agents](/dagster-plus/deployment/deployment-types/hybrid/) with the Dagster+ Agents API.

### Creating agent tokens

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Tokens** tab.
4. Click **+ Create agent token**.

After the token is created:

- **To view a token**, click **Reveal token**. Clicking on the token value will copy it to the clipboard.
- **To edit a token's description**, click the **pencil icon**.

### Assigning agent token permissions

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Tokens** tab.
4. Click **Edit** next to the agent token you'd like to change.

The permissions dialog allows you to edit a token's ability to access certain deployments. By default, agent tokens have permission to access any deployment in the organization including branch deployments. This is called **Org Agent** and is set using the toggle in the top right of the dialog. To edit individual deployment permissions, **Org Agent** has to first be toggled off.

### Revoking agent tokens

To revoke a token:

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Tokens** tab.
4. Click **Edit** next to the agent token you'd like to change.
5. Click **Revoke** in the bottom left of the permissions dialog. When prompted, confirm to proceed with revoking the token.