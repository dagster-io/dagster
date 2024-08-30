---
title: "Team management"
displayed_sidebar: "dagsterPlus"
sidebar_position: 2
---

# Team management in Dagster+

As part of our [role-based access control (RBAC) feature](/dagster-plus/access/rbac/user-roles-permissions), Dagster+ supports the ability to assign users to teams. A team is a group of users with a set of default deployment, code location, and Branch Deployment user roles.

In this guide, we'll cover how to add, manage, and remove teams in Dagster+.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- **The following in Dagster+:**
    - A Pro plan
    - [Organization Admin permissions](/dagster-plus/access/rbac/user-roles-permissions):
      - in your organization
      - for deployments for which you want to manage teams

</details>


## Adding teams

1. In the Dagster+ UI, click the **user menu (your icon) > Organization Settings**.
2. Click the **Teams** tab.
3. Click the **Create a team** button.
4. In the window that displays, enter a name in the **Team name** field.
5. Click **Create team**.

After the team is created, you can [add users and assign user roles to deployments](#managing-team-members-and-roles).


## Managing team members and roles

In the **Organization Settings > Teams** tab:

1. Locate the team you want to modify in the table of teams.
2. Click the **Edit** button in the team's row.

From here, you can [manage team members](#managing-team-members) and [the team's roles for deployments](#managing-team-roles).

### Managing team members

#### Adding team members

1. In the **Members** tab, use the search bar to locate a user in your organization.
2. Once located, click the user.
3. Click **Add user to team**.
4. Repeat as needed, clicking **Done** when finished.

#### Removing team members

1. In the **Members** tab, locate the user in the list of team members.
2. Click **Remove from team**.
3. Repeat as needed, clicking **Done** when finished.

### Managing team roles

1. In the **Roles** tab, click the **Edit team role** button next to the deployment where you want to modify the team's role.
2. In the window that displays, select the team role for the deployment. This [role](/dagster-plus/account/managing-users/managing-user-roles-permissions) will be used as the default for this team for all code locations in the deployment.
3. Click **Save**.
4. To set permissions for individual [code locations](/dagster-plus/account/managing-users/managing-user-roles-permissions#code-locations) in a deployment:
    1. Click the toggle to the left of the deployment to open a list of code locations.
    2. Next to a code location, click **Edit team role**.
    3. Select the team role for the code location.
    4. Click **Save**.

## Removing teams

1. In the Dagster+ UI, click the **user menu (your icon) > Organization Settings**.
2. Click the **Teams** tab.
3. Locate the team you want to delete in the table of teams.
4. Click the **Edit** button in the team's row.
5. Click the **Delete team** button.
6. When prompted, confirm the deletion.

## Next steps

- Learn more about role-based access control (RBAC) in [Understanding User Roles & Permissions](/dagster-plus/access/rbac/user-roles-permissions)
- Learn more about how to manage users in Dagster+ in [Understanding User Management in Dagster+](/dagster-plus/access/rbac/users)