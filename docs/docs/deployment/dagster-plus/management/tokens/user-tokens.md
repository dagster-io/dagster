---
description: Viewing, creating, editing, and revoking user tokens in Dagster+.
sidebar_position: 3100
title: Managing user tokens in Dagster+
tags: [dagster-plus-feature]
---

import ThemedImage from '@theme/ThemedImage';

In this guide, we'll walk you through creating, viewing, editing, and revoking user tokens in Dagster+. The below guide applies to both human users and [service users](/deployment/dagster-plus/authentication-and-access-control/rbac/users#service-users).

## Creating and revoking your own user tokens

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
   ![Organization settings link in user menu](/images/dagster-plus/deployment/management/user-token-management/organization-settings-link.png)
3. Click the **Tokens** tab.
   ![Tokens tab](/images/dagster-plus/deployment/management/user-token-management/tokens-tab.png)

4. Click **+ Create user token**.
   ![Create user token button](/images/dagster-plus/deployment/management/user-token-management/create-user-token.png)

After the token is created:

- **To edit a token's description**, click the **pencil icon** under the "Description" header.
- **To view a token**, click **Reveal token**. Clicking on the token value will copy it to the clipboard.
- **To revoke your own token**, click **Revoke**.

## Revoking another user's tokens

:::info

**Organization Admin** permissions are required to revoke another user's tokens. **Nobody, including Organization Admins, can create a user token for another user or view the value of a user token for another user.**

:::

To revoke an existing token for another user, select the user from the **Manage tokens for** dropdown, then click **Revoke**:

![User token page showing tokens for selected user](/images/dagster-plus/deployment/management/user-token-management/manage-user-tokens-for.png)
