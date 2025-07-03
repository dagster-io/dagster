---
title: 'Real-time insights'
description: Using real-time insights, you can gain visibility into historical asset health and usage metrics.
sidebar_position: 100
---

The Dagster+ observability update includes the next-generation version of Dagster Insights with the following improvements:

- [Real-time metrics](#real-time-metrics)
- [New insights views to help you understand trends](#insights-views)
- [Asset health metrics](#asset-health-metrics)
- [KPI dashboard to help you understand platform health](#kpi-dashboard)

## Real-time metrics

Events now stream back to insights views in real time. Insights views show metrics bucketed by hour through the last 120 days.

## New insights views to help you understand trends \{#insights-views}

To access new insights views, click **Insights** in the top navigation bar in the UI:

![New insights views to understand trends](/images/guides/operate/insights_v2/insights_ui.png)

Key asset health metrics, like materialization and failure count, are prominently displayed. To scope the view to a specific set of assets, type an [asset selection](/guides/build/assets/asset-selection-syntax/reference) in the search bar. Or, to view specific events in a time slice, click a datapoint in the line chart.

The insights view also features activity charts that group events by hour to help you understand scheduling and automation behaviors.

![Activity charts](/images/guides/operate/insights_v2/activity_charts.png)

## Asset health metrics

The UI will continue to display existing [built-in metrics](https://docs.dagster.io/guides/monitor/insights#built-in-metrics) alongside new asset health metrics:

| Metric                               | Description                                                     |
| ------------------------------------ | --------------------------------------------------------------- |
| Time to resolution                   | Duration an asset spent in a failed state before materializing. |
| Materialization success rate         | Percentage of successful executions.                            |
| Materialization failure count        | Number of times an asset failed to materialize.                 |
| Freshness pass rate                  | Percentage of time an asset was fresh.                          |
| Freshness warning and failure counts | Number of times an asset entered a degraded freshness state.    |
| Check success rate                   | Percentage of successful check executions.                      |

## KPI dashboard to help you understand platform health \{#kpi-dashboard}

To access the KPI dashboard, click **Insights** in the top navigation bar in the UI, then navigate to the trends tab:

![KPIs dashboard to understand platform](/images/guides/operate/insights_v2/kpis.png)

KPIs allow you to understand your platform health at a high level, and compare metrics from different saved selections.
