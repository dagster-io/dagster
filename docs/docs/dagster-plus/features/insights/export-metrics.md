---
title: "Export metrics from Dagster+ Insights"
sidebar_label: "Export metrics"
sidebar_position: 200
---

Using a GraphQL API endpoint, you can export [Dagster+ Insights](/dagster-plus/features/insights/) metrics from your Dagster+ instance. 

Refer to the [Built-in Insights metrics](/dagster-plus/features/insights/index.md#built-in-metrics) for a list of available metrics.

## Prerequisites

To complete the steps in this guide, you'll need:

- A Dagster+ account
- Access to the [Dagster+ Insights feature](/dagster-plus/features/insights)
- A Dagster+ [user token](/dagster-plus/deployment/management/tokens/user-tokens)
- Your deployment-scoped Dagster+ deployment URL. For example: `dagster-university.dagster.cloud/prod`

## Before you start

Before you start, note that:

- Metrics are currently computed once per day
- We don't recommend frequently querying over large time ranges that may download a large amount of data. After an initial data load, we recommend loading data daily for the most recent week or less.

## Using the API

In this example, we're using the [GraphQL Python Client](/guides/operate/graphql/graphql-client) to export the Dagster credits metric for all assets for September 2023:

```python
from datetime import datetime
from dagster_graphql import DagsterGraphQLClient

ASSET_METRICS_QUERY = """
query AssetMetrics($metricName: String, $after: Float, $before: Float) {
  reportingMetricsByAsset(
    metricsSelector: {
      metricName: $metricName
      after: $after
      before: $before
      sortAggregationFunction: SUM
      granularity: DAILY
    }
  ) {
    __typename
    ... on ReportingMetrics {
      metrics {
        values
        entity {
          ... on ReportingAsset {
            assetKey {
              path
            }
          }
        }
      }
    }
  }
}

"""


def get_client():
    url = "YOUR_ORG.dagster.cloud/prod"  # Your deployment-scoped url
    user_token = "YOUR_TOKEN"  # A token generated from Organization Settings > Tokens
    return DagsterGraphQLClient(url, headers={"Dagster-Cloud-Api-Token": user_token})


if __name__ == "__main__":
    client = get_client()
    result = client._execute(
        ASSET_METRICS_QUERY,
        {
            "metricName": "__dagster_dagster_credits",
            "after": datetime(2023, 9, 1).timestamp(),
            "before": datetime(2023, 10, 1).timestamp(),
        },
    )

    for asset_series in result["reportingMetricsByAsset"]["metrics"]:
        print("Asset key:", asset_series["entity"]["assetKey"]["path"])
        print("Daily values:", asset_series["values"])

```

To use this example yourself, replace the values of `url` and `user_token` in this function:

```python
def get_client():
    url = "YOUR_ORG.dagster.cloud/prod"  # Your deployment-scoped url
    user_token = "YOUR_TOKEN"  # A token generated from Organization Settings > Tokens
    return DagsterGraphQLClient(url, headers={"Dagster-Cloud-Api-Token": user_token})
```

Refer to the [Reference section](#reference) for more info about the endpoints available in the GraphQL API.

## Reference

For the full GraphQL API reference:

1. Navigate to `YOUR_ORG.dagster.cloud/prod/graphql`, replacing `YOUR_ORG` with your organization name. For example: `https://dagster-university.dagster.cloud/prod/graphql`
2. Click the **Schema** tab.

### Available top-level queries

```graphql
reportingMetricsByJob(
  metricsFilter: JobReportingMetricsFilter
  metricsSelector: ReportingMetricsSelector!
): ReportingMetricsOrError!

reportingMetricsByAsset(
  metricsFilter: AssetReportingMetricsFilter
  metricsSelector: ReportingMetricsSelector!
): ReportingMetricsOrError!

reportingMetricsByAssetGroup(
  metricsFilter: AssetGroupReportingMetricsFilter
  metricsSelector: ReportingMetricsSelector!
): ReportingMetricsOrError!
```

### Specifying metrics and time granularity

Use `metricsSelector` to specify the metric name and time granularity:

```graphql
input ReportingMetricsSelector {
  after: Float # timestamp
  before: Float # timestamp
  metricName: String # see below for valid values
  granularity: ReportingMetricsGranularity
}

enum ReportingMetricsGranularity {
  DAILY
  WEEKLY
  MONTHLY
}

# The valid metric names are:
# "__dagster_dagster_credits"
# "__dagster_execution_time_ms"
# "__dagster_materializations"
# "__dagster_step_failures"
# "__dagster_step_retries"
# "__dagster_asset_check_errors"
# "__dagster_asset_check_warnings"
```
