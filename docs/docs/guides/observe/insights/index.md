---
title: Insights (Dagster+)
description: Using real-toime Dagster+ Insights, you can gain visibility into historical asset health, usage, and cost metrics, such as Dagster+ run duration, credit usage, and failures, and define your own custom metrics, such as the number of rows processed by an asset.
sidebar_position: 500
tags: [dagster-plus-feature]
canonicalUrl: '/guides/observe/insights'
slug: '/guides/observe/insights'
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

Using Dagster+ Insights, you can gain visibility into historical usage and cost metrics such as Dagster+ run duration, credit usage, and failures. You can also define your own custom metrics, such as the number of rows processed by an asset.

Visualizations are built into the Dagster+ UI, allowing you to explore metrics from Dagster and external systems, such as Google BigQuery, in one place.

## Insights benefits

With Insights, you can:

- [Understand platform health with Insights views](#understand-health)
- Compare metrics across asset selections (TK)
- [Integrate additional metrics](#integrate-metrics), like data warehouse cost or your own custom metadata
- [Export metrics](#export-metrics) from Dagster+
- [Create alerts](/guides/observe/alerts) based off of Insights metrics

## Understand platform health with Insights views \{#understand-health}

Insights views can help you understand the health of **Assets**, **Selections**, **Jobs**, and **Deployments**.

You can access Insights views by either

- Clicking **Insights** in the left sidebar, or
- Navigating to a [selection of assets](/guides/build/assets/asset-selection-syntax/reference) in the [asset catalog](/guides/observe/asset-catalog), then clicking **Insights** in the top navigation bar in the UI.

![Insights UI](/images/guides/observe/insights/insights-ui.png)

Key asset health metrics, like materialization and failure count, are prominently displayed for all assets. To scope the view to a specific set of assets, type an [asset selection](/guides/build/assets/asset-selection-syntax/reference) in the search bar. Or, to view specific events in a time slice, click a datapoint in the line chart:

![Click datapoint to view details hover](/images/guides/observe/insights/click-datapoint-to-view-details.png)

![Details of datapoint](/images/guides/observe/insights/datapoint-details.png)

Insights views also features activity charts that group events by hour to help you understand scheduling and automation behaviors:

![Activity charts](/images/guides/observe/insights/activity-charts.png)

For more information on the metrics Dagster provides by default, see the [built-in metrics](#built-in-metrics) section.

:::info

Events now stream back to Insights views in real time. Insights views show metrics bucketed by hour through the last 120 days.

:::

### Known limitations

Since updated Insights views are still under active development, there are a few limitations we aim to address in upcoming releases:

- Health statuses don’t yet take asset observations into account, only materializations
- Failure events and metrics based on them (time to resolution, materialization success rate, and materialization failure count) will not exist prior to the introduction of the new asset metrics
- Insights views do not currently show cost, Dagster credits, and metadata metrics
- The new pages are all asset-focused, and haven’t yet been implemented for jobs

### Data retention

How long historical Insights data is retained depends on your Dagster+ plan:

- **Dagster+ Pro** - 120 days
- **All other plans** - 30 days

### Built-in metrics

#### Assets and selections

| Metric                                | Description                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------------- |
| Materialization success rate          | Percentage of successful executions.                                            |
| Avg. time to resolution               | Duration an asset spent in a failed state before materializing.                 |
| Freshess pass rate                    | Percentage of time an asset was fresh.                                          |
| Check success rate                    | Percentage of successful check executions.                                      |
| Materialization count                 | Number of times an asset was materialized.                                      |
| Failure count                         | Number of times an asset failed to materialize.                                 |
| Step execution time                   |                                                                                 |
| Top assets by retry count             |                                                                                 |
| Top assets by check error count       | The top assets that produced [asset check](/guides/test/asset-checks) errors.   |
| Top assets by check warning count     | The top assets that produced [asset check](/guides/test/asset-checks) warnings. |
| Top assets by freshness failure count | Number of times an asset entered a degraded freshness state.                    |
| Top assets by freshness warning count | Number of times an asset entered a degraded freshness state.                    |

#### Jobs

| Metric                | Description                                                                                                                                                                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Run success count     | The number of successful runs.                                                                                                                                                                                                              |
| Run failure count     | The number of run failures.                                                                                                                                                                                                                 |
| Run duration          | Wall clock time from when a run starts to when it completes. For jobs which run steps in parallel, the run duration may be shorter than the sum of the compute duration for all steps.                                                      |
| Step failures         | The number of times steps failed when computing this object. **Note:** Steps that retry and succeed aren't included in this metric.                                                                                                         |
| Dagster credits       | The Dagster credit cost associated with computing this object. Dagster credits are charged for every step that's run, and for every asset that's materialized. For more information, see the [pricing FAQ](https://dagster.io/pricing#faq). |
| Materializations      | The number of asset materializations associated with computing this object.                                                                                                                                                                 |
| Failed to materialize | The number of materialization failures associated with this object.                                                                                                                                                                         |
| Observations          | The number of [asset observations](/guides/build/assets/metadata-and-tags/asset-observations) associated with computing this object.                                                                                                        |
| Step retries          | The number of times steps were retried when computing this object.                                                                                                                                                                          |

#### Deployments

| Metric           | Description                                                                                                                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dagster credits  | The Dagster credit cost associated with computing this object. Dagster credits are charged for every step that's run, and for every asset that's materialized. For more information, see the [pricing FAQ](https://dagster.io/pricing#faq). |
| Compute duration | The time spent computing steps. For jobs that run steps in parallel, the compute duration may be longer than the wall clock time it takes for the run to complete.                                                                          |
| Run duration     | Wall clock time from when a run starts to when it completes. For jobs which run steps in parallel, the run duration may be shorter than the sum of the compute duration for all steps.                                                      |
| Materializations | The number of asset materializations associated with computing this object.                                                                                                                                                                 |
| Observations     | The number of [asset observations](/guides/build/assets/metadata-and-tags/asset-observations) associated with computing this object.                                                                                                        |
| Step failures    | The number of times steps failed when computing this object. **Note**: Steps that retry and succeed aren't included in this metric.                                                                                                         |

## Integrate other metrics \{#integrate-metrics}

If you are on the Pro plan, you can integration other metrics into Insights, such as asset materialization metadata or Snowflake credits. Insights supports the following additional metrics:

- **[Asset materialization metadata](/guides/observe/insights/asset-metadata)**
- **[Google BigQuery usage](/guides/observe/insights/google-bigquery)** generated by queries made to BigQuery resources or using dbt to materialize tables.
- **[Snowflake usage](/guides/observe/insights/snowflake)** generated by queries made to Snowflake resources or using dbt to materialize tables.

## Export metrics

Metrics in Dagster+ Insights can be exported using a [GraphQL API](/api/graphql) endpoint. For more information, see [Exporting Insights metrics from Dagster+](/guides/observe/insights/export-metrics).
