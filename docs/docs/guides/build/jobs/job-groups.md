---
title: Job groups
description: Job groups organize jobs into named groups, making them easier to navigate in the Dagster UI.
sidebar_position: 350
---

A **job group** is a named collection of jobs. Assigning jobs to groups organizes them in the [Dagster UI](/guides/operate/webserver#dagster-ui-reference), which is useful when a code location contains jobs that serve different purposes, such as jobs that build your main pipeline alongside operational jobs.

Job groups work the same way as asset groups: every job belongs to exactly one group, and jobs defined without a group belong to the `default` group.

## Assigning a job to a group

Pass the `group_name` argument to the <PyObject section="jobs" module="dagster" object="job" decorator /> decorator to assign an [op job](/guides/build/jobs/op-jobs) to a group. In the example below, both jobs belong to the `operational` group:

<CodeExample path="docs_snippets/docs_snippets/guides/build/ops_jobs_graphs/job_groups.py" language="python" startAfter="start_op_job_group" endBefore="end_op_job_group" title="src/<project_name>/defs/jobs.py" />

[Asset jobs](/guides/build/jobs/asset-jobs) accept the same argument. In the example below, `customers_job` belongs to the `analytics` group:

<CodeExample path="docs_snippets/docs_snippets/guides/build/ops_jobs_graphs/job_groups.py" language="python" startAfter="start_asset_job_group" endBefore="end_asset_job_group" title="src/<project_name>/defs/jobs.py" />

`group_name` is also accepted by <PyObject section="graphs" module="dagster" object="GraphDefinition" method="to_job" />, which builds an op job from a graph.

## Nesting groups

Group names can contain one or more segments separated by `/`, which expresses a hierarchy. In the example below, `daily_digest_job` belongs to the `notifications` group nested under `operational`:

<CodeExample path="docs_snippets/docs_snippets/guides/build/ops_jobs_graphs/job_groups.py" language="python" startAfter="start_nested_job_group" endBefore="end_nested_job_group" title="src/<project_name>/defs/jobs.py" />

Each segment of a group name must match the regular expression `^[A-Za-z0-9_]+$`. Leading, trailing, and consecutive separators are not permitted.

The Dagster UI renders each segment as its own collapsible section, so `operational/maintenance` and `operational/notifications` appear as two subgroups nested under a single `operational` section. A group can hold both its own jobs and nested subgroups: if one job is in `operational` and another is in `operational/maintenance`, the `operational` section contains the `maintenance` subgroup followed by its own job.

## Viewing job groups in the Dagster UI

On the **Jobs** page, jobs are listed under a collapsible section for each group within a code location, with nested groups shown as indented sections inside their parent. Collapsing a group hides its jobs and all of its subgroups. Sibling groups are sorted alphabetically, with the `default` group last. If every job in a code location belongs to the `default` group, no group sections are displayed for that code location.

To filter the list by group, use the `group` attribute in the job selection field:

- `group:operational` selects jobs in the `operational` group
- `group:"operational/notifications"` selects jobs in a nested group
- `group:"operational*"` selects jobs in `operational` and all of its nested groups
- `not group:default` excludes jobs that were defined without a group

:::note

Group names that contain a `/` separator must be enclosed in double quotes.

:::

A job's group is also shown in the **Group** section of the sidebar on the job page. This section is hidden for jobs in the `default` group.
