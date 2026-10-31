---
description: The Dagster+ audit log enables Dagster+ Pro organization admins to track and attribute changes to their Dagster deployment with the UI or Dagster+ GraphQL API.
sidebar_position: 8140
tags: [dagster-plus-feature]
title: Viewing and accessing audit logs
---

The Dagster+ audit log enables Dagster+ Pro organizations to track and attribute changes to their Dagster deployment.

For large organizations, tracking down when and by whom changes were made can be crucial for maintaining security and compliance. The audit log is also valuable
for tracking operational history, including sensor and schedule updates.

This guide walks through how to access the audit log and details the interactions which are tracked in the audit log.

:::info Prerequisites

To view or access the Dagster+ audit log, you will need:

- A Dagster+ Pro organization.
- An [Organization Admin](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) role in your Dagster+ organization.

:::

## Viewing audit logs in the UI

To view the audit logs in the UI:

1. As a Dagster+ Pro organization admin, click your user icon at the top right corner of the page.
2. Click **Organization settings**.
3. Click the **Audit log** tab.

Each entry in the audit log indicates when an action was taken, the user who performed the action, the [type of action](#audit-log-entry-types) taken, and the deployment that the action affected. To view additional details for an action, click the **Show** button.

:::tip Filtering the audit log

The **Filter** button near the top left of the page can be used to filter the list of logs. You can filter to a combination of user, event type, affected deployment, or time frame.

:::

## Programmatically accessing audit logs

You can programmatically access audit logs with the Dagster+ [GraphQL API](/api/graphql).

To access a visual GraphiQL interface, visit the GraphQL endpoint in a browser:

- **US region:** `https://<org>.dagster.cloud/<deployment>/graphql`
- **EU region:** `https://<org>.eu.dagster.cloud/<deployment>/graphql`

You can also query the API directly using the Python client:

<CodeExample
  path="docs_snippets/docs_snippets/deployment/dagster_plus/access/rbac/audit-logs.graphql"
  language="graphql"
  title="Audit log GraphQL query"
/>

## Audit log entry types

| Event type                     | Description                                                                                                                            | Additional details                                                        |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Log in                         | A user logs in to the Dagster+ organization                                                                                            |                                                                           |
| Update sensor                  | A user toggles a sensor on or off                                                                                                      | The sensor name, code location, and cursor                                |
| Update schedule                | A user toggles a schedule on or off                                                                                                    | The schedule name, code location, and cursor                              |
| Update alert policy            | A user modifies an [alert policy](/guides/observe/alerts/creating-alerts)                                                              | The new configuration for the alert policy                                |
| Create deployment              | A user creates a new deployment                                                                                                        | Whether the deployment is a branch deployment                             |
| Delete deployment              | A user removes an existing deployment                                                                                                  | Whether the deployment is a branch deployment                             |
| Create user token              | A user creates a new user token                                                                                                        |                                                                           |
| Revoke user token              | A user revokes an existing user token                                                                                                  |                                                                           |
| Create code location           | A user creates a new code location                                                                                                     | The code location name, image, and git metadata                           |
| Update code location           | A user updates an existing code location                                                                                               | The code location name, image, and git metadata                           |
| Delete code location           | A user removes a code location                                                                                                         | The code location name                                                    |
| Change user permissions        | A user alters [permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) for another user   | The permission grant and targeted deployment                              |
| Remove user from organization  | A user removes another user from the Dagster+ organization                                                                             | The removed user's email                                                  |
| Create agent token             | A user creates a new agent token                                                                                                       |                                                                           |
| Revoke agent token             | A user revokes an existing agent token                                                                                                 |                                                                           |
| Create API token               | A user creates an API token, such as the SCIM token an identity provider uses to provision users                                       | The token type and description                                            |
| Revoke API token               | A user revokes an API token                                                                                                            | The token type and description                                            |
| Update agent token permissions | A user alters [permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) for an agent token | The permission grant and targeted deployment                              |
| Create team                    | A user creates a team                                                                                                                  | The team name                                                             |
| Rename team                    | A user renames a team                                                                                                                  | The previous and new team names                                           |
| Delete team                    | A user deletes a team                                                                                                                  | The team name                                                             |
| Change team members            | A user adds a user to, or removes a user from, a team                                                                                  | The team name, the user's email, and whether they were added or removed   |
| Change team permissions        | A user alters [permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) for a team         | The permission grant and targeted deployment                              |
| Create secret                  | A user creates a new [environment variable](/deployment/dagster-plus/management/environment-variables/dagster-ui)                      | The created variable name                                                 |
| Update secret                  | A user modifies an existing [environment variable](/deployment/dagster-plus/management/environment-variables/dagster-ui)               | The previous and current variable names and whether the value was changed |
| Delete secret                  | A user removes an [environment variable](/deployment/dagster-plus/management/environment-variables/dagster-ui)                         | The deleted variable name                                                 |
| Create custom role             | A user creates a custom role                                                                                                           | The role name, description, deployment scope, and permissions             |
| Update custom role             | A user modifies a custom role                                                                                                          | The previous and new name, description, and permissions                   |
| Delete custom role             | A user deletes a custom role                                                                                                           | The role name                                                             |
| Update subscription            | A user modifies the selected Dagster+ subscription for the organization                                                                | The previous and current plan types                                       |
| Update organization settings   | A user changes organization settings, such as the maximum concurrent branch deployment runs                                            | The previous and new values of the settings that changed                  |
