---
title: "User management"
displayed_sidebar: "dagsterPlus"
sidebar_position: 1
---

# User management in Dagster+

In this guide, we'll cover how to add and remove users in your Dagster+ organization.

**Note**: If utilizing [SCIM provisioning](/dagster-plus/access/authentication/scim-provisioning), you'll need to manage users through your Identity Provider (IdP) instead of Dagster+.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- [Organization Admin permissions](/dagster-plus/access/rbac/user-roles-permissions) for your organization in Dagster+

</details>

## Adding users

Before you start, note that:

- **If SCIM provisioning is enabled,** you'll need to add new users in your IdP. Adding users will be disabled in Dagster+.
- **If using Google for SSO**, users must be added in Dagster+ before they can log in.
- **If using an Identity Provider (IdP) like Okta for SSO**, users must be assigned to the Dagster app in the IdP to be able to log in to Dagster+. Refer to the [SSO setup guides](/dagster-plus/access/authentication) for setup instructions for each of our supported IdP solutions.

By default, users will be granted Viewer permissions on each deployment. The default role can be adjusted by modifying the [`sso_default_role` deployment setting](/todo).

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Users** tab.
4. Click **Add new user.**
5. In the **User email** field, enter the user's email address.
6. Click **Add user**. The user will be added to the list of users.

After the user is created, you can [add the user to teams and assign user roles for each deployment](#managing-user-permissions).

## Managing user permissions

After a user is created, the **Manage user permissions** window will automatically display. You can also access this window by clicking **Edit** next to a user in the users table.

TODO: Add picture previously at "/images/dagster-cloud/user-token-management/manage-new-user-permissions.png"

### Adding users to teams

Using the **Teams** field, you can add users to one or more teams. This is useful for centralizing permission sets for different types of users. Refer to the [Managing teams](/dagster-plus/access/rbac/teams) guide for more info about creating and managing teams.

TODO: Add picture previously at "/images/dagster-cloud/user-token-management/add-user-to-teams.png

**Note**: When determining a user's level of access, Dagster+ will use the **most permissive** role assigned to the user between all of their team memberships and any individual role grants. Refer to the [Managing user roles and permissions](/dagster-plus/access/rbac/user-roles-permissions) guide for more info.

### Assigning user roles

In the **Roles** section, you can assign the select the appropriate [user role](/dagster-plus/access/rbac/user-roles-permissions) for each deployment.

1. Next to a deployment, click **Edit user role**.
2. Select the user role for the deployment. This [user role](/dagster-plus/access/rbac/user-roles-permissions) will be used as the default for all code locations in the deployment.
3. Click **Save**.
4. **Pro only**: To set permissions for individual [code locations](/dagster-plus/access/rbac/user-roles-permissions) in a deployment:
    1. Click the toggle to the left of the deployment to open a list of code locations.
    2. Next to a code location, click **Edit user role**.
    3. Select the user role for the code location.
    4. Click **Save**.
5. Repeat the previous steps for each deployment.
6. **Optional**: To change the user's permissions for branch deployments:
    1. Next to **All branch deployments**, click **Edit user role**.
    2. Select the user role to use for all branch deployments.
    3. Click **Save**.
7. Click **Done**.

## Removing users

Removing a user removes them from the organization. **Note**: If using a SAML-based SSO solution like Okta, you'll also need to remove the user from the IdP. Removing the user in Dagster+ doesn't remove them from the IdP.

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Users** tab.
4. Locate the user in the user list.
5. Click **Edit**.
6. Click **Remove user**.
7. When prompted, confirm the removal.


## Next steps

- Learn more about role-based access control (RBAC) in [Understanding User Roles & Permissions](/dagster-plus/access/rbac/user-roles-permissions)
- Learn more about how to manage teams in Dagster+ in [Understanding Team Management in Dagster+](/dagster-plus/access/rbac/teams)
- Learn more about SCIM provisioning in [Understanding SCIM Provisioning](/dagster-plus/access/authentication/scim-provisioning)
- Learn more about authentication in [Understanding Authentication](/dagster-plus/access/authentication)