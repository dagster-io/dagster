---
title: Dagster & dbt Cloud
sidebar_label: dbt Cloud integration
description: Dagster allows you to run dbt Cloud jobs alongside other technologies. You can schedule them to run as a step in a larger pipeline and manage them as a data asset.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
partnerlink:
sidebar_position: 600
---

<p>{frontMatter.description}</p>

Our updated dbt Cloud integration offers two capabilities:

- **Observability** - You can view your dbt Cloud assets in the Dagster Asset Graph and double click into run/materialization history.
- **Orchestration** - You can use Dagster to schedule runs/materializations of your dbt Cloud assets, either on a cron schedule, or based on upstream dependencies.

## Installation

<PackageInstallInstructions packageName="dagster-dbt" />

## Observability example

To make use of the observability capability, you will need to add code to your Dagster project that does the following:

1. Defines your dbt Cloud credentials and workspace.
2. Uses the integration to create asset specs for models in the workspace.
3. Builds a sensor which will poll dbt Cloud for updates on runs/materialization history and dbt Cloud Assets.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_observability.py"
  language="python"
  title="defs/dbt_cloud_observability.py"
/>

## Orchestration example

To make use of the orchestration capability, you will need to add code to your Dagster project that does the following:

1. Defines your dbt Cloud credentials and workspace.
2. Builds your asset graph in a materializable way.
3. Adds these assets to the Declarative Automation Sensor.
4. Builds a sensor to poll dbt Cloud for updates on runs/materialization history and dbt Cloud Assets.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_orchestration.py"
  language="python"
  title="defs/dbt_cloud_orchestration.py"
/>

## Partitioned assets example

You can define partitions alongside your dbt Cloud assets to build incremental models. Pass a `partitions_def` to the `dbt_cloud_assets` decorator, then use `context.partition_time_window` or `context.partition_key` to pass variables to dbt via `--vars`.

When using a `TimeWindowPartitionsDefinition`, a `BackfillPolicy.single_run()` is applied by default.

### Daily partitioned (time window)

Use time window partitions to pass date ranges to your dbt models as variables. This is useful for incremental models that filter by date.

<CodeExample
  startAfter="start_daily_partitioned"
  endBefore="end_daily_partitioned"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_partitioned.py"
  language="python"
  title="defs/dbt_cloud_partitioned.py"
/>

In your dbt model, use the passed variables to filter rows:

```sql
select * from {{ ref('my_model') }}

{% if is_incremental() %}
where order_date >= '{{ var('min_date') }}' and order_date < '{{ var('max_date') }}'
{% endif %}
```

### Static partitioned (e.g. by region)

Use static partitions to run dbt models for different segments like regions or tenants.

<CodeExample
  startAfter="start_static_partitioned"
  endBefore="end_static_partitioned"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_partitioned.py"
  language="python"
  title="defs/dbt_cloud_partitioned.py"
/>

## About dbt Cloud

**dbt Cloud** is a hosted service for running dbt jobs. It helps data analysts and engineers productionize dbt deployments. Beyond dbt open source, dbt Cloud provides scheduling , CI/CD, serving documentation, and monitoring & alerting.

If you're currently using dbt Cloud™, you can also use Dagster to run `dbt-core` in its place. You can read more about [how to do that here](https://dagster.io/blog/migrate-off-dbt-cloud).

---

## Using dbt Cloud with Dagster Components

The `DbtCloudComponent` allows you to load a dbt Cloud project as a set of Dagster assets using the Components API. It automatically synchronizes with your dbt Cloud manifest and triggers jobs remotely.

### Prerequisites

To use this component, you need:

- A dbt Cloud account.
- An API token and Account ID.
- A Project ID and Environment ID for the dbt Cloud project you wish to orchestrate.

### Configuration

The component requires a `workspace` resource and optional selection arguments:

| Argument     | Type                | Description                                                                                           |
| :----------- | :------------------ | :---------------------------------------------------------------------------------------------------- |
| `workspace`  | `DbtCloudWorkspace` | **Required.** Resource containing your dbt Cloud credentials (token, account_id) and project details. |
| `select`     | `str`               | A dbt selection string to filter assets (e.g. `tag:staging`). Defaults to `fqn:*`.                    |
| `exclude`    | `str`               | A dbt selection string to exclude assets.                                                             |
| `defs_state` | `DefsStateConfig`   | Configuration for persisting the state (manifest) locally. Defaults to local filesystem.              |

### Usage Example

```python
from dagster import Definitions
from dagster_dbt import DbtCloudComponent, DbtCloudWorkspace
from dagster.components.utils.defs_state import DefsStateConfigArgs

# Define your dbt Cloud workspace
dbt_cloud_workspace = DbtCloudWorkspace(
    account_id=123456,
    project_id=11111,
    token="your-dbt-cloud-api-token",
)

# Create the component
dbt_cloud = DbtCloudComponent(
    workspace=dbt_cloud_workspace,
    select="fqn:*",
    defs_state=DefsStateConfigArgs.local_filesystem(),
)
```

### YAML Usage

You can also configure the `DbtCloudComponent` directly in YAML using the `{{ env.* }}` template syntax for secrets:

```yaml
type: dagster_dbt.DbtCloudComponent
attributes:
  workspace:
    account_id: 123456
    token: "{{ env.DBT_CLOUD_TOKEN }}"
    access_url: "https://cloud.getdbt.com"
    project_id: 11111
    environment_id: 22222
  select: "tag:dagster"
```

#### Workspace fields

| Field                  | Type    | Default                         | Description                                        |
| :--------------------- | :------ | :------------------------------ | :------------------------------------------------- |
| `account_id`           | `int`   | **Required**                    | The ID of your dbt Cloud account.                  |
| `token`                | `str`   | **Required**                    | Your dbt Cloud API token.                          |
| `access_url`           | `str`   | `https://cloud.getdbt.com`     | Your dbt Cloud workspace URL.                      |
| `project_id`           | `int`   | **Required**                    | The ID of the dbt Cloud project.                   |
| `environment_id`       | `int`   | **Required**                    | The ID of the dbt Cloud environment.               |
| `adhoc_job_name`       | `str`   | Auto-generated                  | Custom name for the ad hoc job created by Dagster.  |
| `request_max_retries`  | `int`   | `3`                             | Maximum number of request retries.                 |
| `request_retry_delay`  | `float` | `0.25`                          | Delay between request retries in seconds.          |
| `request_timeout`      | `int`   | `15`                            | Request timeout in seconds.                        |

### Limitations

Code References: Unlike local dbt projects, the dbt Cloud component does not support linking Dagster assets to local SQL source files, as execution occurs remotely.
