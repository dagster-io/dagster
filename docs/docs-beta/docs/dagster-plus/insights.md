---
title: 'Insights'
description: 'Visiblity into historical usage, cost, and metadata.'
---

# Dagster+ Insights

Using Dagster+ Insights, you can gain visibility into historical usage and cost metrics such as Dagster+ run duration, credit usage, and failures. You can also define your own custom metrics, such as the number of rows processed by an asset.

Visualizations are built into the Dagster+ UI, allowing you to explore metrics from Dagster and external systems, such as Google BigQuery, in one place.

### With Insights, you can

- [Explore usage trends in your Dagster pipelines](#explore-dagsters-built-in-metrics)
- [Integrate additional metrics](#integrate-metrics), like data warehouse cost or your own custom metadata
- [Export metrics](#export-metrics) from Dagster+
- [Create alerts](/dagster-plus/deployment/alerts) based off of Insights metrics TODO: write this alerts section

<details>
  <summary>Prerequisites</summary>

To use Insights, you'll need a Dagster+ account.

</details>

## Explore Dagster's built-in metrics

To access Insights, click **Insights** in the top navigation bar in the UI:

![Viewing the Insights tab in the Dagster+ UI](/img/placeholder.svg)

The left navigation panel on this page contains a list of available metrics. For each metric, the daily, weekly, or monthly aggregated values are displayed in the graph.

Use the tabs above the charts to view metrics for **Assets**, **Asset groups**, **Jobs**, and **Deployments**.

These metrics are updated on a daily basis. Refer to the [Built-in metrics](#built-in-metrics) section for more information about what Dagster provides out of the box.

## Working with Insights metrics \{#insights-metrics}

### Data retention

How long historical Insights data is retained depends on your Dagster+ plan:

- **Dagster+ Pro** - 120 days
- **All other plans** - 30 days

### Built-in metrics

| Metric               | Description                                                                                                                                                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Dagster credits      | The Dagster credit cost associated with computing this object. Dagster credits are charged for every step that's run, and for every asset that's materialized. For more information, [refer to the pricing FAQ](https://dagster.io/pricing#faq). |
| Compute duration     | The time spent computing steps. For jobs that run steps in parallel, the compute duration may be longer than the wall clock time it takes for the run to complete.                                                                               |
| Materializations     | The number of asset materializations associated with computing this object.                                                                                                                                                                      |
| Observations         | The number of [asset observations](/todo) associated with computing this object.                                                                                                                                                                 |
| Step failures        | The number of times steps failed when computing this object. **Note**: Steps that retry and succeed aren't included in this metric.                                                                                                              |
| Step retries         | The number of times steps were retried when computing this object.                                                                                                                                                                               |
| Asset check warnings | The number of [asset checks](/todo) that produced warnings.                                                                                                                                                                                      |
| Asset check errors   | The number of [asset checks](/todo) that produced errors.                                                                                                                                                                                        |
| Retry compute        | The time spent computing steps, including time spent retrying failed steps. For jobs that run steps in parallel, the compute duration may be longer than the wall clock time it takes for the run to complete.                                   |

### Integrate other metrics \{#integrate-metrics}

Users on the Pro plan can integration other metrics into Insights, such as asset materialization metadata or Snowflake credits. Insights supports the following additional metrics:

- **Asset materialization metadata.** Refer to the [Using asset metadata with Dagster+ Insights guide](/dagster-plus/insights/asset-metadata) for more info.
- [**Google BigQuery usage**](/dagster-plus/insights/google-bigquery) generated by either queries made to BigQuery resources or using dbt to materialize tables
- [**Snowflake usage**](/dagster-plus/insights/snowflake) generated by either queries made to Snowflake resources or using dbt to materialize tables

### Export metrics

Metrics in Dagster+ Insights can be exported using a GraphQL API endpoint. Refer to the [Exporting Insights metrics from Dagster+ guide](/dagster-plus/insights/export-metrics) for details.
