---
title: Databricks (Component)
sidebar_label: Databricks
description: The dagster-databricks library provides a DatabricksWorkspaceComponent to represent Databricks jobs as assets.
tags: [dagster-supported, component, databricks]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-databricks
pypi: https://pypi.org/project/dagster-databricks
sidebar_custom_props:
  logo: images/integrations/databricks.svg
partnerlink: https://databricks.com/
slug: /integrations/libraries/databricks
---

import Beta from '@site/docs/partials/_Beta.md';

<Beta />

The `dagster-databricks` library provides the `DatabricksWorkspaceComponent`, which allows you to automatically discover Databricks jobs and represent them as assets in Dagster.

This component is state-backed, meaning it fetches metadata from your Databricks workspace and caches it to avoid repeated API calls.

## Loading Databricks Jobs

You can use the `DatabricksWorkspaceComponent` to load jobs from your workspace.
Note: Tasks belonging to the same Databricks Job are grouped into a single Dagster Multi-Asset. This ensures that when you materialize the asset, the entire Databricks Job runs, preserving shared state between tasks.

Filtering Jobs
You can filter which jobs are included by providing a list of job IDs. Only the specified jobs will be represented as assets.

```yaml
type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: "{{ env.DATABRICKS_HOST }}"
    token: "{{ env.DATABRICKS_TOKEN }}"

type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: "{{ env.DATABRICKS_HOST }}"
    token: "{{ env.DATABRICKS_TOKEN }}"
  databricks_filter:
    include_jobs:
      job_ids: [12345, 67890]
```

Customizing Assets
By default, asset keys are generated from the task name. You can override the key, group, and description for specific tasks using assets_by_task_key.

```yaml
type: dagster_databricks.DatabricksWorkspaceComponent
attributes:
  workspace:
    host: '{{ env.DATABRICKS_HOST }}'
    token: '{{ env.DATABRICKS_TOKEN }}'
  assets_by_task_key:
    ingest_data_task:
      - key: 'clean_ingestion'
        group: 'etl_pipeline'
        description: 'Ingests data from S3 to Delta Lake'
```

Legacy Resources
For information on using the legacy Pythonic resources (`DatabricksClientResource`) and ops, see the [Pythonic Resources](/integrations/libraries/databricks/pythonic-resources) page.
