---
title: Insights (Dagster+)
description: Using real-time Dagster+ Insights, you can gain visibility into historical asset health, usage, and cost metrics, such as Dagster+ run duration and failures.
sidebar_position: 500
tags: [dagster-plus-feature]
canonicalUrl: '/guides/observe/insights'
slug: '/guides/observe/insights'
---

import Beta from '@site/docs/partials/\_Beta.md';
import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';

<DagsterPlus />

<Beta />

Using Dagster+ Insights, you can gain visibility into historical usage and trends, such as execution time, success rate, and time to resolving failures. You can also build custom reports to compare different deployments or selections of assets against each other to quickly identify issues across your data platform.

With Insights, you can:

- [Understand platform health with real-time Insights views](#understand-health)
- [Compare metrics across asset selections](#compare-metrics)
- [Create alerts](/guides/observe/alerts) based off of Insights metrics

## Understand platform health with real-time Insights views \{#understand-health}

Real-time Insights views can help you understand the health of **Assets**, **Selections**, **Jobs**, and **Deployments**.

To access Insights views, you can either:

- Click **Insights** in the left sidebar, or
- Navigate to a [selection of assets](/guides/build/assets/asset-selection-syntax/reference) in the [asset catalog](/guides/observe/asset-catalog), then click **Insights** in the top navigation bar.

![Insights UI](/images/guides/observe/insights/insights-ui.png)

Key asset health metrics, like materialization and failure count, are prominently displayed for assets and selections, and additional metrics are displayed for jobs and deployments. Historical Insights data can be queried for up to 30 days.

For a full list of metrics, see the [supported metrics](#supported-metrics) section.

To limit the view to a specific set of assets, type an [asset selection](/guides/build/assets/asset-selection-syntax/reference) in the search bar. Or, to view specific events in a time slice, hover over a datapoint in the line chart, then click to view details:

![Click datapoint to view details hover](/images/guides/observe/insights/click-datapoint-to-view-details.png)

![Details of datapoint](/images/guides/observe/insights/datapoint-details.png)

Insights views also features activity charts that group events by hour to help you understand scheduling and automation behaviors:

![Activity charts](/images/guides/observe/insights/activity-charts.png)

:::info Limitations

Since updated Insights views are still under active development, there are a few limitations we aim to address in upcoming releases:

- Insights views do not currently show cost, Dagster credits, and metadata metrics

:::

## Compare metrics across asset selections \{#compare-metrics}

Insights views allow you to compare metrics across all assets, or a chosen subset of saved asset selections.

To compare metrics across specific selections, navigate to the **Selections** tab, then click **Choose a selection**. You can choose up to five saved selections:

![Choose a selection dropdown](/images/guides/observe/insights/choose-selection.png)

To remove a selection from comparison, click the three dots menu on the selection column, then click **Remove from grid**:

![Remove selection from grid](/images/guides/observe/insights/remove-selection.png)

To choose which metrics to compare across selections, click **Choose metrics**, then check the metrics you'd like to include:

![Choose metrics dropdown](/images/guides/observe/insights/choose-metrics.png)

### Supported metrics

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

## Export metrics

:::info

Support for exporting metrics is coming soon in updated Insights. To use legacy Insights, toggle off "New homepage & observability UIs" in your user settings.

:::

Metrics in Dagster+ Insights can be exported using a [GraphQL API](/api/graphql) endpoint. For more information, see [Export metrics from Dagster+](/guides/observe/insights/export-metrics).
