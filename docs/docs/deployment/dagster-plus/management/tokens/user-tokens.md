---
description: Viewing, creating, editing, and revoking user tokens in Dagster+.
sidebar_position: 3100
title: Managing user tokens in Dagster+
---

import ThemedImage from '@theme/ThemedImage';

In this guide, we'll walk you through creating user tokens in Dagster+.

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
  style={{width: '100%', height: 'auto'}}
  sources={{
    light: '/images/dagster-plus/deployment/management/user-token-management/manage-user-tokens-for.png',
    dark: '/images/dagster-plus/deployment/management/user-token-management/manage-user-tokens-for.png',
  }}
/>

:::note
**Organization Admin** permissions are required to manage another user's tokens.
:::
