---
title: Asset jobs
sidebar_position: 100
---

Jobs are the main unit of execution and monitoring for [asset definitions](/guides/build/assets/defining-assets) in Dagster. An asset job is a type of job that targets a [selection of assets](/guides/build/assets/asset-selection-syntax) and can be launched:

- Manually from the Dagster UI
- At fixed intervals, by [schedules](/guides/automate/schedules)
- When external changes occur, using [sensors](/guides/automate/sensors)

## Creating asset jobs

In this section, we'll demonstrate how to create a few asset jobs that target the following assets:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-jobs/asset-jobs.py" language="python" startAfter="start_marker_assets" endBefore="end_marker_assets" />

To create an asset job, use the [`define_asset_job`](/api/python-api/assets#dagster.define_asset_job) method. An asset-based job is based on the assets the job targets and their dependencies.

You can target one or multiple assets, or create multiple jobs that target overlapping sets of assets. In the following example, we have two jobs:

- `all_assets_job` targets all assets
- `sugary_cereals_job` targets only the `sugary_cereals` asset

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-jobs/asset-jobs.py" language="python" startAfter="start_marker_jobs" endBefore="end_marker_jobs" />

## Making asset jobs available to Dagster tools

Including the jobs in a [`Definitions`](/api/python-api/definitions) object located at the top level of a Python module or file makes asset jobs available to the UI, GraphQL, and the command line. The Dagster tool loads that module as a code location. If you include schedules or sensors, the [code location](/guides/deploy/code-locations) will automatically include jobs that those schedules or sensors target.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/jobs_to_definitions.py" />

## Testing asset jobs

Dagster has built-in support for testing, including separating business logic from environments and setting explicit expectations on uncontrollable inputs. For more information, see the [testing documentation](/guides/test).

## Executing asset jobs

You can run an asset job in a variety of ways:

- In the Python process where it's defined
- Via the command line
- Via the GraphQL API
- In the UI

## Examples

The [Hacker News example](https://github.com/dagster-io/dagster/tree/master/examples/project_fully_featured) [builds an asset job that targets an asset group](https://github.com/dagster-io/dagster/blob/master/examples/project_fully_featured/project_fully_featured/jobs.py).
