---
title: 'User roles & permissions'
displayed_sidebar: 'dagsterPlus'
sidebar_position: 3
---

# Understanding user roles & permissions in Dagster+

Role-based access control (RBAC) enables you to grant specific permissions to users in your organization, ensuring that Dagster users have access to what they require in Dagster+, and no more.

In this guide, we'll cover how RBAC works in Dagster+, how to assign roles to users, and the granular permissions for each user role.

<details>
  <summary>Prerequisites</summary>

To complete the steps in this guide, you'll need:

- A Dagster+ account
  - Additionally, in certain cases listed below, a Dagster+ Pro plan

</details>

## Dagster+ user roles

Dagster+ uses a hierarchical model for RBAC, meaning that the most permissive roles include permissions from the roles beneath them. The following user roles are currently supported, in order from the **most** permissive to the **least** permissive:

- Organization Admin
- Admin
- Editor
- Launcher (Pro plans only)
- Viewer

For example, the **Admin** user role includes permissions specific to this role and all permissions in the **Editor**, **Launcher**, and **Viewer** user roles. Refer to the [User permissions reference](#user-permissions-reference) for the full list of user permissions in Dagster+.

### User role enforcement

All user roles are enforced both in Dagster+ and the GraphQL API.

### Teams

Dagster+ Pro users can create teams of users and assign default permission sets. Refer to the [Managing teams in Dagster+](/dagster-plus/access/rbac/teams) guide for more info.

## Assigning user and team roles

With the exception of the **Organization Admin** role, user and team roles are set on a per-deployment basis.

Organization Admins have access to the entire organization, including all [deployments](/todo), [code locations](/dagster-plus/deployment/code-locations), and [Branch Deployments](/dagster-plus/deployment/branch-deployments).

| Level              | Plan      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------ | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Deployment         | All plans | Defines the level of access for a given deployment. Roles set at this level will be the default role for the user or team for all code locations in the deployment. <br/><br/> <strong>Note</strong>: Granting access to a deployment grants a minimum of <strong>Viewer</strong> access to all code locations. Preventing access for specific code locations isn't currently supported. Additionally, having access to a deployment doesn't grant access to Branch Deployments - those permissions must be granted separately.                      |
| Code location      | Pro       | Defines the level of access for a given code location in a deployment. <br/><br/> Dagster+ Pro users can [override the default deployment-level role for individual code locations](/dagster-plus/deployment/code-locations). For example, if the <strong>Deployment</strong> role is <strong>Launcher</strong>, you could override this role with a more permissive role, such as <strong>Editor</strong> or <strong>Admin</strong>. <br/><br/> For non-Pro users, users will have the same level of access for all code locations in a deployment. |
| Branch deployments | All plans | Defines the level of access for all Branch Deployments in the code locations the user or team has access to.                                                                                                                                                                                                                                                                                                                                                                                                                                         |

### Applying role overrides

As previously mentioned, you can define individual user roles for users in your organization.

Dagster+ Pro users can also apply permission overrides to grant specific exceptions.

Overrides may be used to apply a **more permissive** role. If, for example, the default role is **Admin** or **Organization Admin**, overrides will be disabled as these are the most permissive roles.

#### Code locations

To override a code location role for an individual user:

1. Locate the user in the list of users.
2. Click **Edit**.
3. Click the toggle to the left of the deployment to open a list of code locations.
4. Next to a code location, click **Edit user role**.
5. Select the user role for the code location:
   - TODO: add picture previously at "/images/dagster-cloud/user-token-management/code-location-override.png"
6. Click **Save**.

#### Team members

Users in your organization can belong to one or more [teams](/dagster-plus/access/rbac/teams). When determining a user's level of access, Dagster+ will use the **most permissive** role assigned to the user between all of their team memberships and any individual role grants.

For example, let's look at a user with the following roles for our `dev` deployment:

- **Team 1**: Launcher
- **Team 2**: Viewer
- **Individual**: Viewer

In this example, the user would have **Launcher** access to the `prod` deployment. This is because the Launcher role is more permissive than Viewer.

The above also applies to code locations and Branch Deployment roles.

#### Viewing overrides

To view deployment-level overrides for a specific user, locate the user on the **Users** page and hover over a deployment:

TODO: add picture previously at "/images/dagster-cloud/user-token-management/user-overrides-popup.png"

If there are code location-level overrides, a small **N override(s)** link will display beneath the user's deployment role. Hover over it to display the list of overrides:

TODO: add picture previously at "/images/dagster-cloud/user-token-management/code-location-override-popup.png"

#### Removing overrides

1. Locate the user in the list of users.
2. Click **Edit**.
3. To remove an override:
   - **For a deployment**, click **Edit user role** next to the deployment.
   - **For a code location**, click the toggle next to the deployment to display a list of code locations. Click **Edit user role** next to the code location.
4. Click the **Remove override** button.
5. Click **Save**.

## User permissions reference

### General

|                                                                          | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| ------------------------------------------------------------------------ | ------ | -------- | ------ | ----- | ------------------------ |
| View runs of [jobs](/concepts/ops-jobs)                                  | ✅     | ✅       | ✅     | ✅    | ✅                       |
| Launch, re-execute, terminate, and delete runs of jobs                   | ❌     | ✅       | ✅     | ✅    | ✅                       |
| Start and stop [schedules](/concepts/schedules)                          | ❌     | ❌       | ✅     | ✅    | ✅                       |
| Start and stop [schedules](/concepts/sensors)                            | ❌     | ❌       | ✅     | ✅    | ✅                       |
| Wipe assets                                                              | ❌     | ❌       | ✅     | ✅    | ✅                       |
| Launch and cancel [schedules](/guides/backfill) | ❌     | ✅       | ✅     | ✅    | ✅                       |
| Add dynamic partitions                                                   | ❌     | ❌       | ✅     | ✅    | ✅                       |

### Deployments

Deployment settings are accessed in the UI by navigating to **user menu (your icon) > Organization Settings > Deployments**.

|                                                                                              | Viewer | Launcher  | Editor | Admin | Organization <br/> admin     |
|----------------------------------------------------------------------------------------------|-------|-----------|--------|-------|-------------------------------|
| View [deployments](/todo)                                           | ✅     | ✅         | ✅      | ✅     | ✅                             |
| Modify [deployment](/todo) settings                                 | ❌     | ❌         | ✅      | ✅     | ✅                             |
| Create, edit, delete [environment variables](/dagster-plus/deployment/environment-variables) | ❌     | ❌         | ✅      | ✅     | ✅                             |
| View [environment variable](/dagster-plus/deployment/environment-variables)  values          | ❌     | ❌         | ✅      | ✅     | ✅                             |
| Export [environment variables](/dagster-plus/deployment/environment-variables)               | ❌     | ❌         | ✅      | ✅     | ✅                             |
| Create and delete [deployments](/todo)                              | ❌     | ❌         | ❌      | ❌     | ✅                             |
| Create [Branch Deployments](/dagster-plus/deployment/branch-deployments)                     | ❌     | ❌         | ✅      | ✅     | ✅                             |

### Code locations

Code locations are accessed in the UI by navigating to **Deployment > Code locations**.

|                                                                                 | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| ------------------------------------------------------------------------------- | ------ | -------- | ------ | ----- | ------------------------ |
| View [code locations](/dagster-plus/deployment/code-locations)                  | ✅     | ✅       | ✅     | ✅    | ✅                       |
| Create and remove [code locations](/dagster-plus/deployment/code-locations)     | ❌     | ❌       | ✅     | ✅    | ✅                       |
| Reload [code locations](/dagster-plus/deployment/code-locations) and workspaces | ❌     | ❌       | ✅     | ✅    | ✅                       |

### Agent tokens

Agent tokens are accessed in the UI by navigating to **user menu (your icon) > Organization Settings > Tokens**.

|                                                             | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| ----------------------------------------------------------- | ------ | -------- | ------ | ----- | ------------------------ |
| View [agent tokens](/dagster-plus/deployment/hybrid/tokens) | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Create agent tokens                                         | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Edit agent tokens                                           | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Revoke agent tokens                                         | ❌     | ❌       | ❌     | ❌    | ✅                       |

### User tokens

User tokens are accessed in the UI by navigating to **user menu (your icon) > Organization Settings > Tokens**.

|                                          | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| ---------------------------------------- | ------ | -------- | ------ | ----- | ------------------------ |
| View and create own [user tokens](/todo) | ✅     | ✅       | ✅     | ✅    | ✅                       |
| List all user tokens                     | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Revoke all user tokens                   | ❌     | ❌       | ❌     | ❌    | ✅                       |

### Users

User management is accessed in the UI by navigating to **user menu (your icon) > Organization Settings > Users**.

|                                               | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| --------------------------------------------- | ------ | -------- | ------ | ----- | ------------------------ |
| [View users](/dagster-plus/access/rbac/users) | ✅     | ✅       | ✅     | ✅    | ✅                       |
| Add users                                     | ❌     | ❌       | ❌     | ✅    | ✅                       |
| Edit user roles                               | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Remove users                                  | ❌     | ❌       | ❌     | ❌    | ✅                       |

### Teams

Team management is accessed in the UI by navigating to **user menu (your icon) > Organization Settings > Teams**.

**Note**: Admin users can modify teams only in deployments where they're an Admin.

|                                               | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| --------------------------------------------- | ------ | -------- | ------ | ----- | ------------------------ |
| [View teams](/dagster-plus/access/rbac/teams) | ✅     | ✅       | ✅     | ✅    | ✅                       |
| Modify team permissions                       | ❌     | ❌       | ❌     | ✅    | ✅                       |
| Create teams                                  | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Re-name teams                                 | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Add/remove team members                       | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Remove teams                                  | ❌     | ❌       | ❌     | ❌    | ✅                       |

### Workspace administration

|                                                        | Viewer | Launcher | Editor | Admin | Organization <br/> admin |
| ------------------------------------------------------ | ------ | -------- | ------ | ----- | ------------------------ |
| Manage [alerts](/dagster-plus/deployment/alerts)       | ❌     | ❌       | ✅     | ✅    | ✅                       |
| Edit workspace                                         | ❌     | ❌       | ✅     | ✅    | ✅                       |
| [Administer SAML](/dagster-plus/access/authentication) | ❌     | ❌       | ❌     | ❌    | ✅                       |
| [Manage SCIM](/todo)                                   | ❌     | ❌       | ❌     | ❌    | ✅                       |
| View usage                                             | ❌     | ❌       | ❌     | ❌    | ✅                       |
| Manage billing                                         | ❌     | ❌       | ❌     | ❌    | ✅                       |
| View audit logs                                        | ❌     | ❌       | ❌     | ❌    | ✅                       |

## Next steps

- Learn more about how to manage users in Dagster+ in [Understanding User Management in Dagster+](/dagster-plus/access/rbac/users)
- Learn more about how to manage teams in Dagster+ in [Understanding Team Management in Dagster+](/dagster-plus/access/rbac/teams)
- Learn more about SCIM provisioning in [Understanding SCIM Provisioning](/todo)
- Learn more about authentication in [Understanding Authentication](/dagster-plus/access/authentication)
