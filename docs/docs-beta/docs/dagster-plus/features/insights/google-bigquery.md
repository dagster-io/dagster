---
title: 'Track Google BigQuery usage with Dagster+ Insights'
sidebar_label: 'Google BigQuery'
sidebar_position: 400
---

Dagster allows you to track external metrics, such as BigQuery usage in the Insights UI. Out of the box integrations are provided to capture query runtime and billed usage, and associate them with the relevant assets or jobs.

:::note
The BigQuery cost metric is based off of the bytes billed for queries executed with Dagster, based on a unit price of $6.25 per TiB.
:::

## Requirements

To use these features, you will need:

- A Dagster+ account on the **Pro** plan
- Access to the [Dagster+ Insights feature](/dagster-plus/features/insights)
- BigQuery credentials which have access to the **`INFORMATION_SCHEMA.JOBS`** table, such as a BigQuery Resource viewer role.
  - For more information, see the [BigQuery Documentation](https://cloud.google.com/bigquery/docs/information-schema-jobs)
- The following packages installed:

```bash
pip install dagster dagster-cloud
```

## Limitations

- Up to two million individual data points may be added to Insights, per month
- External metrics data will be retained for 120 days
- Insights data may take up to 24 hours to appear in the UI

## Tracking usage with the BigQueryResource

The `dagster-cloud` package provides an `InsightsBigQueryResource`, which is a drop-in replacement for the `BigQueryResource` provided by `dagster-gcp`.

This resource will emit BigQuery usage metrics to the Dagster+ Insights API whenever it makes a query.

To enable this behavior, replace usage of `BigQueryResource` with `InsightsBigQueryResource`.

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      filePath="dagster-plus/insights/google-bigquery/bigquery-resource.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      filePath="dagster-plus/insights/google-bigquery/bigquery-resource-insights.py"
      language="python"
    />
  </TabItem>
</Tabs>

## Tracking usage with dagster-dbt

If you use `dagster-dbt` to manage a dbt project that targets Google BigQuery, you can emit usage metrics to the Dagster+ API with the `DbtCliResource`.

First, add a `.with_insights()` call to your `dbt.cli()` command(s).

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      filePath="dagster-plus/insights/google-bigquery/bigquery-dbt-asset.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      filePath="dagster-plus/insights/google-bigquery/bigquery-dbt-asset-insights.py"
      language="python"
    />
  </TabItem>
</Tabs>

Then, add the following to your `dbt_project.yml`:

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      filePath="dagster-plus/insights/google-bigquery/dbt_project.yml"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After" default>
    <CodeExample
      filePath="dagster-plus/insights/google-bigquery/dbt_project_insights.yml"
      language="python"
    />
  </TabItem>
</Tabs>

This adds a comment to each query, which is used by Dagster+ to attribute cost metrics to the correct assets.
