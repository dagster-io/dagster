---
title: "Team management"
displayed_sidebar: "dagsterPlus"
sidebar_position: 2
---

# Team management in Dagster+

As part of [role-based access control (RBAC)](/dagster-plus/access/rbac/user-roles-permissions), Dagster+ supports the ability to assign users to teams. A team is a group of users with a set of default deployment, code location, and Branch Deployment user roles.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- A Dagster+ Pro plan
- Dagster+ [Organization Admin permissions](/dagster-plus/access/rbac/user-roles-permissions):
   - In your organization, and
   - For the deployments where you want to manage teams

</details>


## Adding teams

1. In the Dagster+ UI, click the **user menu (your icon) > Organization Settings**.
2. Click the **Teams** tab.
3. Click the **Create a team** button.
4. In the window that displays, enter a name in the **Team name** field.
5. Click **Create team**.

After the team is created, you can [add team members](#adding-team-members) and [assign user roles to deployments](#managing-team-roles).

## Adding team members

Navigate to the **Organization Settings > Teams** tab and locate the team you want to add team members to. Then:

1. Click the **Edit** button in the **Actions** column.
2. In the **Members** tab, use the search bar to locate a user in your organization.
3. Once located, click the user.
4. Click **Add user to team**.
5. Repeat as needed, clicking **Done** when finished.

## Removing team members

Navigate to the **Organization Settings > Teams** tab and locate the team you want to remove team members from. Then:

1. Click the **Edit** button in the **Actions** column.
2. In the **Members** tab, locate the user in the list of team members.
3. Click **Remove from team**.
4. Repeat as needed, clicking **Done** when finished.

## Managing team roles

Navigate to the **Organization Settings > Teams** tab and locate the team you want to manage roles for. Then:

1. Click the **Edit** button in the **Actions** column.
2. In the **Roles** tab, click the **Edit team role** button next to the deployment where you want to modify the team's role.
3. In the window that displays, select the team role for the deployment. This [role](/dagster-plus/access/rbac/user-roles-permissions) will be used as the default for this team for all code locations in the deployment.
4. Click **Save**.
5. To set permissions for individual [code locations](/dagster-plus/access/rbac/user-roles-permissions) in a deployment:
    1. Click the toggle to the left of the deployment to open a list of code locations.
    2. Next to a code location, click **Edit team role**.
    3. Select the team role for the code location.
    4. Click **Save**.

## Removing teams

Navigate to the **Organization Settings > Teams** tab and locate the team you want to remove. Then:

1. Click the **Edit** button in the **Actions** column.
2. In the modal that displays, click the **Delete team** button.
3. When prompted, confirm the deletion.

## Next steps

- Learn more about RBAC in [Understanding User Roles & Permissions](/dagster-plus/access/rbac/user-roles-permissions)
- Learn more about how to manage users in Dagster+ in [Understanding User Management in Dagster+](/dagster-plus/access/rbac/users)
