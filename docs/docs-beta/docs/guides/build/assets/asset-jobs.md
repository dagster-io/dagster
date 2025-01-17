---
title: Asset jobs
sidebar_position: 900
---

Jobs are the main unit of execution and monitoring for [asset definitions](/guides/build/assets/defining-assets) in Dagster. An asset job is a type of job that targets a selection of assets and can be launched:

- Manually from the Dagster UI
- At fixed intervals, by [schedules](/guides/automate/schedules)
- When external changes occur, using [sensors](/guides/automate/sensors)


## Creating asset jobs

In this section, we'll demonstrate how to create a few asset jobs that target the following assets:

{/* Original code example in https://github.com/dagster-io/dagster/blob/master/examples/docs_snippets/docs_snippets/concepts/assets/non_argument_deps.py between start_marker and end_marker */}
<CodeExample filePath="" language="python" lineStart="" lineEnd=""/>

To create an asset job, use the [`define_asset_job`](/api/python-api/assets#dagster.define_asset_job) method. An asset-based job is based on the assets the job targets and their dependencies.

You can target one or multiple assets, or create multiple jobs that target overlapping sets of assets. In the following example, we have two jobs:

- `all_assets_job` targets all assets
- `sugary_cereals_job` targets only the `sugary_cereals` asset

{/* Original code example in https://github.com/dagster-io/dagster/blob/master/examples/docs_snippets/docs_snippets/concepts/assets/build_job.py between start_marker and end_marker */}
<CodeExample filePath="" language="python" lineStart="" lineEnd=""/>

## Making asset jobs available to Dagster tools

Including the jobs in a [`Definitions`](/api/python-api/definitions) object located at the top level of a Python module or file makes asset jobs available to the UI, GraphQL, and the command line. The Dagster tool loads that module as a code location. If you include schedules or sensors, the [code location](/guides/deploy/code-locations) will automatically include jobs that those schedules or sensors target.

```python file=/concepts/assets/jobs_to_definitions.py
from dagster import Definitions, MaterializeResult, asset, define_asset_job


@asset
def number_asset():
    yield MaterializeResult(
        metadata={
            "number": 1,
        }
    )


number_asset_job = define_asset_job(name="number_asset_job", selection="number_asset")

defs = Definitions(
    assets=[number_asset],
    jobs=[number_asset_job],
)
```

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
