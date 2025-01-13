---
title: 'Okta SCIM provisioning'
sidebar_position: 200
unlisted: true
---

The [System for Cross-domain Identity Management specification](https://scim.cloud/) (SCIM) is a standard designed to manage user identity information. When enabled in Dagster+, SCIM allows you to efficiently and easily manage users in your Identity Provider (IdP) - in this case, Okta - and sync their information to Dagster+.

In this guide, we'll walk you through configuring [Okta SCIM provisioning](https://developer.okta.com/docs/concepts/scim/) for Dagster+.

## About this feature

<Tabs>
<TabItem value="Supported features">

### Supported features

With Dagster+'s Okta SCIM provisioning feature, you can:

- **Create users**. Users that are assigned to the Dagster+ application in the IdP will be automatically added to your Dagster+ organization.
- **Update user attributes.** Updating a user's name or email address in the IdP will automatically sync the change to your user list in Dagster+.
- **Remove users.** Deactivating or unassigning a user from the Dagster+ application in the IdP will remove them from the Dagster+ organization
{/* - **Push user groups.** Groups and their members in the IdP can be pushed to Dagster+ as [Teams](/dagster-plus/account/managing-users/managing-teams). */}
- **Push user groups.** Groups and their members in the IdP can be pushed to Dagster+ as
    [Teams](/todo).

Refer to [Okta's SCIM documentation](https://developer.okta.com/docs/concepts/scim/) for more information about Okta's SCIM offering.

</TabItem>
<TabItem value="Limitations">

### Limitations

Dagster+ currently supports the following attributes for SCIM syncing:

- `user.firstName`
- `user.lastName`
- `user.email`, which must match the user's username in Okta
- `user.displayName`

</TabItem>
</Tabs>

## Prerequisites

To complete the steps in this guide, you'll need:

{/* - **To have set up Okta SSO for Dagster+.** Refer to the [Okta SSO setup guide](/dagster-plus/account/authentication/okta/saml-sso) for more info. */}
- **To have set up Okta SSO for Dagster+.** Refer to the [Okta SSO setup guide](/todo) for more info.
- **Permissions in Okta that allow you to configure applications.**
- **The following in Dagster+:**
  - A Pro plan
  {/* - [Organization Admin permissions](/dagster-plus/account/managing-users/managing-user-roles-permissions#user-permissions-reference) in your organization */}
  - [Organization Admin permissions](/todo) in your organization

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

{/* 3. Click the Dagster+ app. **Note**: If you haven't set up SSO for Okta, [follow this guide](/dagster-plus/account/authentication/okta/saml-sso)) to do so before continuing. */}
3. Click the Dagster+ app. **Note**: If you haven't set up SSO for Okta, [follow this guide](/todo)) to do so before continuing.

4. Click the **Sign On** tab and complete the following:

   1. Click **Edit**.

   2. In the **Advanced Sign-on Settings** section, enter the name of your organization in the **Organization** field.

   3. In the **Credential Details** section, set the **Application username format** field to **Email**:


    ![Configured Sign On tab of Dagster+ Okta application](/images/dagster-cloud/sso/okta/scim-sign-on-tab.png)

   4. Click **Save**.

5. Click the **Provisioning** tab and complete the following:

   1. Click **Configure API Integration**.

   2. Check the **Enable API integration** checkbox that displays.

   3. In the **API Token** field, paste the Dagster+ API token you generated in [Step 1](#step-1-enable-scim-provisioning-in-dagster):

    ![Configured Provisioning tab of Dagster+ Okta application](/images/dagster-cloud/sso/okta/provisioning-tab.png)

   4. Click **Test API Credentials** to verify that your organization and API token work correctly.

   5. When finished, click **Save**.

## Step 3: Enable user syncing in Okta

After you confirm that your API credentials work in the Dagster+ Okta application, you can enable user syncing:

1. In the Dagster+ Okta app, click the **Provisioning** tab.

2. In the **Settings** panel, click **To App**.

3. Click **Edit**.

4. Next to **Create Users**, check the **Enable** checkbox:

    ![Highlighted Create users setting and default username setting in Okta](/images/dagster-cloud/sso/okta/provisioning-to-app-create-users.png)

   **Note**: The default username used to create accounts must be set to **Email** or user provisioning may not work correctly.

5. Optionally, check **Enable** next to **Update User Attributes** and **Deactivate Users** to enable these features.

6. When finished, click **Save**.

## Step 4: Enable group syncing in Okta

{/*
:::note
  This step is required only if you want to sync Okta user groups to Dagster+ as [Teams](/dagster-plus/account/managing-users/managing-teams).
:::
*/}
:::note
  This step is required only if you want to sync Okta user groups to Dagster+ as [Teams](/todo).
:::

{/* When **Push groups** is enabled in Okta, you can sync user groups from Okta to Dagster+ as [Teams](/dagster-plus/account/managing-users/managing-teams). Refer to the [Okta documentation](https://help.okta.com/oie/en-us/Content/Topics/users-groups-profiles/usgp-enable-group-push.htm) for setup instructions. */}
When **Push groups** is enabled in Okta, you can sync user groups from Okta to Dagster+ as [Teams](/todo). Refer to the [Okta documentation](https://help.okta.com/oie/en-us/Content/Topics/users-groups-profiles/usgp-enable-group-push.htm) for setup instructions.

## Next steps

That's it! Once Okta successfully syncs users to Dagster+, synced users will have a 'synced' icon next to them in the Dagster+ users page:

    ![Synced/external user icon next to user in Dagster+ user list](/images/dagster-cloud/sso/dagster-cloud-external-user.png)

{/* Refer to the [Utilizing SCIM provisioning guide](/dagster-plus/account/authentication/utilizing-scim-provisioning) for more info about how user and team management works when SCIM provisioning is enabled. */}
Refer to the [Utilizing SCIM provisioning guide](/todo) for more info about how user and team management works when SCIM provisioning is enabled.

## Related

{/* - [Utilizing SCIM provisioning](/dagster-plus/account/authentication/utilizing-scim-provisioning) */}
- [Utilizing SCIM provisioning](/todo)
{/* - [Setting up Okta SSO](/dagster-plus/account/authentication/okta/saml-sso) */}
- [Setting up Okta SSO](/todo)
{/* - [Managing user roles and permissions](/dagster-plus/account/managing-users/managing-user-roles-permissions) */}
- [Managing user roles and permissions](/todo)
{/* - [Managing teams](/dagster-plus/account/managing-users/managing-teams) */}
- [Managing teams](/todo)
{/* - [Managing users](/dagster-plus/account/managing-users) */}
- [Managing users](/todo)
