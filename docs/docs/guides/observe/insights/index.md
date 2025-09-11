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

- [Understand trends in the health of assets, selections, jobs, and deployments](#insights-trends)
- [Understand platform health across asset selections with the KPI dashboard](#kpi-dashboard)
- [Integrate additional metrics](#integrate-metrics), like data warehouse cost or your own custom metadata
- [Export metrics](#export-metrics) from Dagster+
- [Create alerts](/guides/observe/alerts) based off of Insights metrics

## Understand trends in the health of assets, selections, jobs, and deployments \{#insights-trends}

Insights can help you understand trends in **Assets**, **Selections**, **Jobs**, and **Deployments**.

To access Insights, either click **Insights** in the left sidebar, or navigate to a selection of assets in the asset catalog, then click **Insights** in the top navigation bar in the UI:

![New insights views](/images/guides/operate/insights_v2/insights_ui.png)

Key asset health metrics, like materialization and failure count, are prominently displayed for all assets. To scope the view to a specific set of assets, type an [asset selection](/guides/build/assets/asset-selection-syntax/reference) in the search bar. Or, to view specific events in a time slice, click a datapoint in the line chart.

The insights view also features activity charts that group events by hour to help you understand scheduling and automation behaviors:

![Activity charts](/images/guides/operate/insights_v2/activity_charts.png)

These metrics are updated on daily. For more information on the metrics Dagster provides by default, see the [built-in metrics](#built-in-metrics) section.

:::info

Events now stream back to insights views in real time. Insights views show metrics bucketed by hour through the last 120 days.

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

| Metric                               | Description                                                                                                                                                                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dagster credits                      | The Dagster credit cost associated with computing this object. Dagster credits are charged for every step that's run, and for every asset that's materialized. For more information, see the [pricing FAQ](https://dagster.io/pricing#faq). |
| Compute duration                     | The time spent computing steps. For jobs that run steps in parallel, the compute duration may be longer than the wall clock time it takes for the run to complete.                                                                          |
| Materializations                     | The number of asset materializations associated with computing this object.                                                                                                                                                                 |
| Observations                         | The number of [asset observations](/guides/build/assets/metadata-and-tags/asset-observations) associated with computing this object.                                                                                                        |
| Step failures                        | The number of times steps failed when computing this object.<br /> **Note**: Steps that retry and succeed aren't included in this metric.                                                                                                   |
| Step retries                         | The number of times steps were retried when computing this object.                                                                                                                                                                          |
| Asset check warnings                 | The number of [asset checks](/guides/test/asset-checks) that produced warnings.                                                                                                                                                             |
| Asset check errors                   | The number of [asset checks](/guides/test/asset-checks) that produced errors.                                                                                                                                                               |
| Retry compute                        | The time spent computing steps, including time spent retrying failed steps. For jobs that run steps in parallel, the compute duration may be longer than the wall clock time it takes for the run to complete.                              |
| Materialization success rate         | Percentage of successful executions.                                                                                                                                                                                                        |
| Avg. time to resolution              | Duration an asset spent in a failed state before materializing.                                                                                                                                                                             |
| Freshness pass rate                  | Percentage of time an asset was fresh.                                                                                                                                                                                                      |
| Check success rate                   | Percentage of successful check executions.                                                                                                                                                                                                  |
| Materialization failure count        | Number of times an asset failed to materialize.                                                                                                                                                                                             |
| Freshness warning and failure counts | Number of times an asset entered a degraded freshness state.                                                                                                                                                                                |

## Understand platform health across asset selections with the KPI dashboard \{#kpi-dashboard}

The new KPI dashboard helps you understand platform health at a high level across saved asset selections. To access it, click **Insights** in the left sidebar, then navigate to the **Trends** tab:

![KPI dashboard](/images/guides/operate/insights_v2/kpis.png)

## Integrate other metrics \{#integrate-metrics}

If you are on the Pro plan, you can integration other metrics into Insights, such as asset materialization metadata or Snowflake credits. Insights supports the following additional metrics:

- **[Asset materialization metadata](/guides/observe/insights/asset-metadata)**
- **[Google BigQuery usage](/guides/observe/insights/google-bigquery)** generated by queries made to BigQuery resources or using dbt to materialize tables.
- **[Snowflake usage](/guides/observe/insights/snowflake)** generated by queries made to Snowflake resources or using dbt to materialize tables.

## Export metrics

Metrics in Dagster+ Insights can be exported using a [GraphQL API](/api/graphql) endpoint. For more information, see [Exporting Insights metrics from Dagster+](/guides/observe/insights/export-metrics).
