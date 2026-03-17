---
title: Custom metrics
description: Define custom metrics from asset metadata to track any numeric value in Dagster+ Insights, including historical aggregation and alerting.
sidebar_label: Custom metrics
sidebar_position: 5000
tags: [dagster-plus-feature]
---

import DagsterPlus from '@site/docs/partials/\_DagsterPlus.md';
import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<DagsterPlus />

<EarlyAccess />

**Custom metrics** let you track any numeric asset metadata in Dagster+ Insights. Unlike [built-in metrics](/guides/observe/insights) such as run duration and failure counts, custom metrics are defined by you and powered by the numeric metadata your assets emit at runtime. Metric values are ingested in near real-time and displayed as time series alongside built-in metrics in the Insights UI.

## Prerequisites

- A Dagster+ account
- The **Editor** role or above in your deployment

## Step 1: Emit numeric metadata on your assets

Custom metrics are backed by asset metadata. You'll need one or more assets that emit the same metadata key with numeric (int or float) values at materialization or observation time.

For example, the following asset emits a `processing_time_ms` metric each time it materializes:

```python
import dagster as dg

@dg.asset
def my_table():
    elapsed_ms = 1500  # your logic here
    return dg.MaterializeResult(
        metadata={"processing_time_ms": elapsed_ms}
    )
```

For more details, see [the metadata guide](/guides/build/assets/metadata-and-tags#runtime-metadata).

## Step 2: Create a custom metric

1. In the Dagster UI, navigate to **Deployment** > **Custom metrics**.
2. Click **Add custom metric**.
3. Fill in the following fields:
   - **Metadata key** (required) — must exactly match the metadata key your assets emit. This field cannot be changed after creation.
   - **Display name** (optional) — a human-readable name shown in the Insights UI.
   - **Description** (optional) — additional context about what the metric tracks.

:::note

- Each deployment supports up to 500 custom metrics.
- Non-numeric metadata values for a registered key do not count against this limit.

:::

## Step 3: View custom metrics in Insights UI

Once created, custom metrics appear alongside built-in metrics in the Insights UI. In the Insights sidebar navigation, custom metrics are grouped under the **User provided metrics** category.

## Monitoring custom metrics with alerts

You can create [alert policies](/guides/observe/alerts) to monitor your custom metrics:

1. In Dagster, navigate to **Deployment** > **Alert policies** and click **Create alert policy**.
2. Select **Asset** as the alert type.
3. Choose **Metrics** as the event type.
4. Select your custom metric from the metric dropdown.
5. Configure thresholds (greater than or less than a value).

For the full list of alert configuration options, see [Creating alert policies](/guides/observe/alerts/creating-alerts).

## Managing custom metrics

You can edit a custom metric's display name and description at any time from the **Deployment** > **Custom metrics** page in Dagster. The metadata key cannot be changed after creation — to track a different key, create a new metric.

To delete a custom metric, click the menu on the metric row and select **Delete**. Deleting a metric removes it from Insights views but does not affect the underlying asset metadata.

:::note Permissions

Those with **Editor** role and above can create, edit, and delete custom metrics. **Viewer** and **Launcher** roles can view custom metrics in Insights, but cannot modify them.

:::
