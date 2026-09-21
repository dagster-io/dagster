---
title: Configuring concurrency for branch deployments
description: Control how many runs can execute concurrently across and within branch deployments using organization-scoped Dagster+ settings.
sidebar_position: 7345
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Unlike [full deployments](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference#concurrency-concurrency), which each have their own concurrency settings, branch deployments share a single set of concurrency settings that are configured at the **organization** level and apply to every branch deployment in your organization.

This guide describes each of the available settings and how they interact.

## Available settings

Branch deployment concurrency is controlled by three organization-scoped settings:

| Setting                                     | Scope                                    | Default       | Description                                                                                                               |
| ------------------------------------------- | ---------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `max_concurrent_branch_deployment_runs`     | Global across **all** branch deployments | `50`          | Caps the total number of runs that can be in progress at the same time across every branch deployment.                    |
| `max_concurrent_runs_per_branch_deployment` | Per **individual** branch deployment     | `null` (none) | Caps the number of runs that can be in progress within a single branch deployment.                                        |
| `branch_deployment_tag_concurrency_limits`  | Global across **all** branch deployments | `[]`          | Caps the number of runs with particular run tags that can be in progress at the same time across every branch deployment. |

All three settings apply only to branch deployments. Full deployments are configured independently using [full deployment settings](/deployment/dagster-plus/deploying-code/full-deployments/full-deployment-settings-reference#concurrency-concurrency).

### `max_concurrent_branch_deployment_runs` (global)

Caps the total number of in-progress runs across **all** branch deployments in the organization. Once this limit is reached, additional runs in any branch deployment will remain queued until an in-progress run finishes.

- **Default:** `50`
- **Maximum:** `500` on [Hybrid](/deployment/dagster-plus/hybrid), `50` on [Serverless](/deployment/dagster-plus/serverless). Contact Support to request an increase.
- **Minimum:** `0` (setting to `0` prevents any runs in branch deployments from launching). Negative values are not allowed.

Use this setting to cap the total resource usage of branch deployments — for example, to prevent a large number of concurrent pull requests from overwhelming shared infrastructure.

### `max_concurrent_runs_per_branch_deployment` (per branch deployment)

Caps the number of in-progress runs within any single branch deployment. This limit is applied independently to each branch deployment.

- **Default:** `null` (no per-deployment limit; only the global limit applies)
- **Minimum:** `0`. Must be less than or equal to `max_concurrent_branch_deployment_runs`.

This setting does **not** supersede `max_concurrent_branch_deployment_runs` — both limits apply at the same time. A run in a branch deployment is only dequeued if neither limit has been reached. For example, with `max_concurrent_branch_deployment_runs: 50` and `max_concurrent_runs_per_branch_deployment: 5`, no single branch deployment can have more than 5 runs in progress at once, and the total across all branch deployments still cannot exceed 50.

Use this setting to prevent a single pull request from consuming all of the available branch deployment capacity.

### `branch_deployment_tag_concurrency_limits` (global)

Applies concurrency limits to branch deployment runs based on run tags. Limits are enforced across **all** branch deployments combined.

- **Default:** `[]` (no tag-based limits)

Each entry in the list has the following properties:

- `key`: The run tag key to match.
- `value` (optional): Either a specific tag value to match, or `{applyLimitPerUniqueValue: true}` to apply the limit independently to each unique value seen for the key.
- `limit`: The maximum number of in-progress runs that match the tag.

Use this setting to enforce limits on runs that share a tag across branch deployments — for example, capping how many runs targeting a particular external database can execute at once.

## Editing the settings

Branch deployment concurrency settings are organization-scoped and can be edited from the Dagster+ UI or with the `dg` CLI. Either method requires the [Organization Admin role](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions#dagster-user-roles).

The sample YAML below sets all three settings at once:

```yaml
max_concurrent_branch_deployment_runs: 100
max_concurrent_runs_per_branch_deployment: 10
branch_deployment_tag_concurrency_limits:
  - key: 'database'
    value: 'redshift'
    limit: 5
  - key: 'team'
    value:
      applyLimitPerUniqueValue: true
    limit: 3
```

<Tabs>
<TabItem value="Dagster+" label="Dagster+ UI">

To edit organization settings in the Dagster+ UI:

1. Sign in to your Dagster+ account.
2. Click your **user icon > Organization Settings**.
3. Click the **Advanced** tab.
4. Edit the organization settings YAML to set the desired values.
5. Click **Save changes**.

</TabItem>
<TabItem value="dg" label="dg CLI" default>

Before running these commands, [log in to your Dagster+ organization](/api/clis/dg-cli/configuring-dagster-plus) with `dg plus login` using a user token that has the Organization Admin role.

To view the current organization settings:

```bash
dg api organization settings get
```

To modify the settings, first save them to a YAML file on your local system:

```bash
dg api organization settings get > org-settings.yaml
```

Edit the file to set the desired values, then apply the changes:

```bash
dg api organization settings set org-settings.yaml
```

</TabItem>
</Tabs>

## Viewing active limits in the UI

When a run is queued in a branch deployment, you can click the **View queue criteria** link under the run ID in the Dagster+ UI to see which concurrency limits are being applied, including both the global and per-branch-deployment caps.
