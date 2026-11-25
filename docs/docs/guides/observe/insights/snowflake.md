---
description: Track Snowflake usage metrics with the Dagster+ Insights UI or the dagster-cloud package.
sidebar_label: Snowflake
sidebar_position: 2000
title: Track Snowflake usage with Dagster+ Insights
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Dagster+ lets you track external metrics, such as Snowflake usage, in the Insights UI. The Snowflake integrations associate estimated warehouse compute credits with your assets or jobs.

## Requirements

To use these features, you will need:

- A [Dagster+](/deployment/dagster-plus) account on the **Pro** plan
- Access to the [Dagster+ Insights feature](/guides/observe/insights)
- A Snowflake connection for the scheduled importer with access to the `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` view. If you use Snowflake database roles, an administrator can grant `SNOWFLAKE.GOVERNANCE_VIEWER` to the account role used by the connection. See the [Snowflake database role reference](https://docs.snowflake.com/en/sql-reference/snowflake-db-roles#database-role-required-to-access-account-usage-views).
- The following packages installed:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    ```bash uv add dagster dagster-cloud dagster-snowflake ```
  </TabItem>
  <TabItem value="pip" label="pip">
    ```bash pip install dagster dagster-cloud dagster-snowflake ```
  </TabItem>
</Tabs>

## Limitations

- The scheduled importer reads `EXECUTION_TIME` and `WAREHOUSE_SIZE` from `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY`. It estimates compute credits by multiplying execution time in hours by a fixed hourly credit rate based on warehouse size. It uses rates for X-Small through 4X-Large and omits queries that report larger warehouse sizes. The estimate excludes warehouse idle time and other charges, such as storage and serverless compute, so it can differ from your Snowflake bill.
- Up to two million individual data points may be added to Insights, per month
- External metrics data will be retained for 120 days
- Insights data may take up to 24 hours to appear in the UI

## Tracking usage with the SnowflakeResource

The `dagster-cloud` package provides an `InsightsSnowflakeResource`, which is a drop-in replacement for the `SnowflakeResource` provided by `dagster-snowflake`.

This resource adds SQL comments so the scheduled importer can attribute estimated compute credits to the relevant Dagster assets or jobs.

To enable this behavior, replace usage of `SnowflakeResource` with `InsightsSnowflakeResource`, and add Snowflake-specific insights definitions to your code using `create_snowflake_insights_asset_and_schedule`.

These additional definitions are required because Snowflake usage information is only available after a delay. These definitions automatically handle running a computation on a schedule to ingest Snowflake usage information from the previous hour.

:::note
Only use `create_snowflake_insights_asset_and_schedule` in a single code location per deployment, as this will handle ingesting usage data from your entire deployment.
:::

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/observe/insights/snowflake/snowflake-resource.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      path="docs_snippets/docs_snippets/guides/observe/insights/snowflake/snowflake-resource-insights.py"
      language="python"
    />
  </TabItem>
</Tabs>

## Tracking usage with dagster-dbt

If you use `dagster-dbt` to manage a dbt project that targets Snowflake, you can use `DbtCliResource` and query comments to associate Snowflake compute credits with your Dagster assets.

Snowflake usage information is only available after a delay. You must add Snowflake-specific insights definitions to your code using `create_snowflake_insights_asset_and_schedule`, which automatically handles running a computation on a schedule to ingest Snowflake usage information from the previous hour.

:::note
Only use `create_snowflake_insights_asset_and_schedule` in a single code location per deployment, as this will handle ingesting usage data from your entire deployment.
:::

### Using DbtProjectComponent

If you use `DbtProjectComponent`, add `insights` to the `include_metadata` list in your `defs.yaml`:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: path/to/dbt_project
  include_metadata:
    - insights
```

### Using @dbt_assets

If you use the `@dbt_assets` decorator, add a `.with_insights()` call to your `dbt.cli()` command(s):

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/observe/insights/snowflake/snowflake-dbt-asset.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      path="docs_snippets/docs_snippets/guides/observe/insights/snowflake/snowflake-dbt-asset-insights.py"
      language="python"
    />
  </TabItem>
</Tabs>

### Configuring dbt_project.yml

Add the following to your `dbt_project.yml`:

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample path="docs_snippets/docs_snippets/guides/observe/insights/snowflake/dbt_project.yml" language="python" />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample path="docs_snippets/docs_snippets/guides/observe/insights/snowflake/dbt_project_insights.yml" language="python" />
    This adds a comment to each query, which is used by Dagster+ to attribute cost metrics to the correct assets.
  </TabItem>

</Tabs>
