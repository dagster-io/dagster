---
description: Configure SCIM provisioning in Dagster+ to sync user information between Okta and your Dagster+ deployment.
sidebar_position: 8310
title: Configuring Okta SCIM provisioning
sidebar_label: Okta
tags: [dagster-plus-feature]
---

In this guide, we'll walk you through configuring [Okta SCIM provisioning](https://developer.okta.com/docs/concepts/scim) for Dagster+.

:::info Limitations

Dagster+ currently supports the following attributes for SCIM syncing:

- `user.firstName`
- `user.lastName`
- `user.email`, which must match the user's username in Okta
- `user.displayName`

:::

## Prerequisites

To complete the steps in this guide, you'll need:

- **To have set up Okta SSO for Dagster+.** For more information, see the [Okta SSO setup guide](/deployment/dagster-plus/authentication-and-access-control/sso/okta-sso).
- **Permissions in Okta that allow you to configure applications.**
- **The following in Dagster+:**
  - A Pro plan
  - [Organization Admin permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) in your organization

## Step 1: Enable SCIM provisioning in Dagster+

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Provisioning** tab.
4. If SCIM provisioning isn't enabled, click the **Enable SCIM provisioning** button to enable it.
5. Click **Create SCIM token** to create an API token. This token will be used to authenticate requests from Okta to Dagster+.

Keep the API token handy - you'll need it in the next step.

## Step 2: Enable SCIM provisioning in Okta

1. Sign in to your Okta Admin Dashboard.

2. Using the sidebar, click **Applications > Applications**.

3. Click the Dagster+ app. **Note**: If you haven't set up SSO for Okta, [follow this guide](/deployment/dagster-plus/authentication-and-access-control/sso/okta-sso) to do so before continuing.

4. Click the **Sign On** tab and complete the following:

   1. Click **Edit**.

   2. In the **Advanced Sign-on Settings** section, enter the name of your organization in the **Organization** field.

   3. In the **Credential Details** section, set the **Application username format** field to **Email**:

   ![Configured Sign On tab of Dagster+ Okta application](/images/dagster-plus/features/authentication-and-access-control/okta/scim-sign-on-tab.png)

   4. Click **Save**.

5. Click the **Provisioning** tab and complete the following:

   1. Click **Configure API Integration**.

   2. Check the **Enable API integration** checkbox that displays.

   3. In the **API Token** field, paste the Dagster+ API token you generated in [Step 1](#step-1-enable-scim-provisioning-in-dagster):

   ![Configured Provisioning tab of Dagster+ Okta application](/images/dagster-plus/features/authentication-and-access-control/okta/provisioning-tab.png)

   4. Click **Test API Credentials** to verify that your organization and API token work correctly.

   5. When finished, click **Save**.

## Step 3: Enable user syncing in Okta

After you confirm that your API credentials work in the Dagster+ Okta application, you can enable user syncing:

1. In the Dagster+ Okta app, click the **Provisioning** tab.

2. In the **Settings** panel, click **To App**.

3. Click **Edit**.

4. Next to **Create Users**, check the **Enable** checkbox:

   ![Highlighted Create users setting and default username setting in Okta](/images/dagster-plus/features/authentication-and-access-control/okta/provisioning-to-app-create-users.png)

   **Note**: The default username used to create accounts must be set to **Email** or user provisioning may not work correctly.

5. Optionally, check **Enable** next to **Update User Attributes** and **Deactivate Users** to enable these features.

6. When finished, click **Save**.

## Step 4: Enable group syncing in Okta

:::note

This step is required only if you want to sync Okta user groups to Dagster+ as [Teams](/deployment/dagster-plus/authentication-and-access-control/rbac/teams).

:::

{/* When **Push groups** is enabled in Okta, you can sync user groups from Okta to Dagster+ as [Teams](/deployment/dagster-plus/authentication-and-access-control/rbac/managing-users/managing-teams). Refer to the [Okta documentation](https://help.okta.com/oie/en-us/Content/Topics/users-groups-profiles/usgp-enable-group-push.htm) for setup instructions. */}
When **Push groups** is enabled in Okta, you can sync user groups from Okta to Dagster+ as [Teams](/deployment/dagster-plus/authentication-and-access-control/rbac/teams). Refer to the [Okta documentation](https://help.okta.com/oie/en-us/Content/Topics/users-groups-profiles/usgp-enable-group-push.htm) for setup instructions.

Once Okta successfully syncs users to Dagster+, synced users will have a 'synced' icon next to them in the Dagster+ users page:

![Synced/external user icon next to user in Dagster+ user list](/images/dagster-plus/features/authentication-and-access-control/dagster-cloud-external-user.png)

## Next steps

For more information on how user and team management works when SCIM provisioning is enabled, see the [main page of this section](/deployment/dagster-plus/authentication-and-access-control/scim).
