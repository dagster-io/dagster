---
title: 'Track Snowflake usage with Dagster+ Insights'
sidebar_label: 'Snowflake'
sidebar_position: 300
---

Dagster allows you to track external metrics, such as Snowflake usage, in the Insights UI. Out of the box integrations are provided to capture query runtime and billed usage, and associate them with the relevant assets or jobs.

## Requirements

To use these features, you will need:

- A Dagster+ account on the **Pro** plan
- Access to the [Dagster+ Insights feature](/dagster-plus/features/insights)
- Snowflake credentials which have access to the **`snowflake.account_usage.query_history`**.
  - For more information, see the [Snowflake Documentation](https://docs.snowflake.com/en/sql-reference/account-usage#enabling-the-snowflake-database-usage-for-other-roles)
- The following packages installed:

```bash
pip install dagster dagster-cloud dagster-snowflake
```

## Limitations

- Up to two million individual data points may be added to Insights, per month
- External metrics data will be retained for 120 days
- Insights data may take up to 24 hours to appear in the UI

## Tracking usage with the SnowflakeResource

The `dagster-cloud` package provides an `InsightsSnowflakeResource`, which is a drop-in replacement for the `SnowflakeResource` provided by `dagster-snowflake`.

This resource will emit Snowflake usage metrics to the Dagster+ Insights API whenever it makes a query.

To enable this behavior, replace usage of `SnowflakeResource` with `InsightsSnowflakeResource`, and add Snowflake-specific insights definitions to your code using `create_snowflake_insights_asset_and_schedule`.

These additional definitions are required because Snowflake usage information is only available after a delay. These definitions automatically handle running a computation on a schedule to ingest Snowflake usage information from the previous hour.

:::note
Only use `create_snowflake_insights_asset_and_schedule` in a single code location per deployment, as this will handle ingesting usage data from your entire deployment.
:::

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      filePath="dagster-plus/insights/snowflake/snowflake-resource.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      filePath="dagster-plus/insights/snowflake/snowflake-resource-insights.py"
      language="python"
    />
  </TabItem>
</Tabs>

## Tracking usage with dagster-dbt

If you use `dagster-dbt` to manage a dbt project that targets Snowflake, you can emit usage metrics to the Dagster+ API with the `DbtCliResource`.

First, add a `.with_insights()` call to your `dbt.cli()` command(s), and add Snowflake-specific insights definitions to your code using `create_snowflake_insights_asset_and_schedule`.

These additional definitions are required because Snowflake usage information is only available after a delay. These definitions automatically handle running a computation on a schedule to ingest Snowflake usage information from the previous hour.

:::note
Only use `create_snowflake_insights_asset_and_schedule` in a single code location per deployment, as this will handle ingesting usage data from your entire deployment.
:::

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      filePath="dagster-plus/insights/snowflake/snowflake-dbt-asset.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      filePath="dagster-plus/insights/snowflake/snowflake-dbt-asset-insights.py"
      language="python"
    />
  </TabItem>
</Tabs>

Then, add the following to your `dbt_project.yml`:

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample filePath="dagster-plus/insights/snowflake/dbt_project.yml" language="python" />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample filePath="dagster-plus/insights/snowflake/dbt_project_insights.yml" language="python" />
    This adds a comment to each query, which is used by Dagster+ to attribute cost metrics to the correct assets.
  </TabItem>

</Tabs>
