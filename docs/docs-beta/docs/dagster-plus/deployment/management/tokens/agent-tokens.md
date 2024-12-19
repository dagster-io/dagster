---
title: 'Agent tokens'
sidebar_position: 200
unlisted: true
---

import ThemedImage from '@theme/ThemedImage';

# Managing user and agent tokens in Dagster+

:::note
This guide is applicable to Dagster+.
:::

In this guide, we'll walk you through creating and revoking user and agent tokens in Dagster+.

## Managing agent tokens
:::note
To manage agent tokens, you need to be an{" "}
<a href="/dagster-plus/account/managing-users">Organization Admin</a> in
Dagster+.
:::

Agent tokens are used to authenticate [Hybrid agents](/dagster-plus/deployment/agents) with the Dagster+ Agents API.

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

## Managing user tokens

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Tokens** tab.
4. Click **+ Create user token**.

After the token is created:

- **To edit a token's description**, click the **pencil icon**.
- **To view a token**, click **Reveal token**. Clicking on the token value will copy it to the clipboard.
- **To revoke a token**, click **Revoke**.

To manage tokens for another user, select the user from the **Manage tokens for** dropdown:

<ThemedImage
  style={{width:'100%', height: 'auto'}}
  sources={{
    light: '/images/dagster-cloud/user-token-management/manage-user-tokens-for.png',
    dark: '/images/dagster-cloud/user-token-management/manage-user-tokens-for.png',
  }}
/>

:::note
**Organization Admin** permissions are required to manage another user's tokens.
:::