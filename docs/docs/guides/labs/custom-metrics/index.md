---
title: 'Custom Metrics'
description: 'Track numeric asset metadata as time-series metrics in Dagster Insights'
tags: [dagster-plus-feature]
canonicalUrl: '/guides/labs/custom-metrics'
slug: '/guides/labs/custom-metrics'
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

Dagster Insights automatically tracks standard metrics like run duration, step duration, and row count from asset materializations. **Custom metrics** let you go beyond these built-in metrics and track business-specific numeric values — things like API tokens consumed, downloads processed, or records synced to a third-party service.

To create a custom metric, you choose a metadata key that your assets already emit during materialization or observation and register it as a tracked metric through the Dagster UI. Once registered, its numeric values are captured as time-series data and you can configure alerts against them.

Custom metrics appear in the **Insights** page under the **User provided metrics** section in the left navigation, and as an available metric type when creating alert policies.

## Prerequisites

- The **Editor** role or above in your Dagster+ deployment

## Configuring custom metrics

To register a metadata key as a custom metric:

1. Navigate to **Insights** in the left sidebar.
2. Click the **Edit** link next to the **User provided metrics** heading, or click the settings gear icon to open **Insights settings**.
3. In the **Metrics display** tab, you will see a table of metadata keys from your asset materializations and observations.
4. Click the **visibility toggle** (eye icon) next to a key to register it as a tracked custom metric.

Once registered, the metric will appear in the left nav and its values will be captured as time-series data going forward.

:::note
New metadata values will be available the next time Insights data is ingested, which typically happens within minutes. Newly enabled metrics may show a **pending** badge until the first data point is ingested.
:::

## Customizing metric display

You can customize how each metric appears in the UI:

1. In the **Metrics display** settings table, click the **Edit** button for a metric.
2. Set a **display name** to replace the raw metadata key (e.g., "Anthropic Tokens" instead of `anthropic_tokens_used`).
3. Add a **description** to help your team understand what the metric tracks.
4. Click the **checkmark** to save.

The display name will be used in the Insights left navigation and when selecting metrics in alert policies.

## Where custom metrics appear

Once registered, custom metrics are visible in two places:

- **Insights left navigation:** Each visible metric appears under "User provided metrics" with its display name.
- **Alert policies:** Custom metrics are available as a metric type when creating asset alert policies in **Deployment > Alerts**.

## Limits

| Constraint | Value |
|------------|-------|
| Maximum custom metrics per deployment | 500 |
| Supported value types | Numeric only (`int`, `float`) |
| Metadata key uniqueness | One metric per key per deployment |

Non-numeric metadata values are silently skipped. After a custom metric is created, its metadata key cannot be changed — only the display name and description can be updated.
