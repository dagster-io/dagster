---
title: "Checking for data freshness"
sidebar_position: 20
sidebar_label: "Data freshness"
---

Freshness checks provide a way to identify data assets that are overdue for an update. For example, you can use freshness checks to identify stale assets caused by:

- The pipeline hitting an error and failing
- Runs not being scheduled
- A backed up run queue
- Runs taking longer than expected to complete

Freshness checks can also communicate SLAs for their data freshness. For example, downstream asset consumers can determine how often assets are expected to be updated by looking at the defined checks.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need familiarity with:

- [Assets](/guides/data-assets)
- [External assets](/guides/external-assets)
- [Asset checks](/guides/asset-checks)

</details>

## Getting started

To get started with freshness checks, follow these general steps:

1. **Define a freshness check**: Freshness checks are defined using `build_last_update_freshness_checks`, which utilizes an asset's last updated time to determine freshness.

   **If using Dagster+ Pro**, you can also use [`build_anomaly_detection_freshness_checks`](#anomaly-detection) to define a freshness check that uses an anomaly detection model to determine freshness.
2. **Define a schedule or sensor**: Defining a schedule or sensor (`build_sensor_for_freshness_checks`) is required to ensure the freshness check executes. If the check only runs after the asset has been materialized, the check won't be able to detect the times materialization fails.
3. **Pass the freshness check and schedule/sensor to the `Definitions` object**: Freshness checks and the associated schedule or sensor must be added to a `Definitions` object for Dagster to recognize them.
4. **View the freshness check results in the Dagster UI**: Freshness check results will appear in the UI, allowing you to track the results over time.

## Materializable asset freshness \{#materializable-assets}

Materializable assets are assets materialized by Dagster. To calculate whether a materializable asset is overdue, Dagster uses the asset's last materialization timestamp.

The example below defines a freshness check on an asset that fails if the asset's latest materialization occurred more than one hour before the current time.

<CodeExample filePath="guides/data-assets/quality-testing/freshness-checks/materializable-asset-freshness-check.py" language="python" />

## External asset freshness \{#external-assets}

[External assets](/guides/external-assets) are assets orchestrated by systems other than Dagster.

To run freshness checks on external assets, the checks need to know when the external assets were last updated. Emitting these update timestamps as values for the `dagster/last_updated_timestamp` observation metadata key allows Dagster to calculate whether the asset is overdue.

The example below defines a freshness check and adds a schedule to run the check periodically.

<CodeExample filePath="guides/data-assets/quality-testing/freshness-checks/external-asset-freshness-check.py" language="python" />

### Testing freshness with anomaly detection \{#anomaly-detection}

:::note
Anomaly detection is a Dagster+ Pro feature.
:::

Instead of applying policies on an asset-by-asset basis, Dagster+ Pro users can use `build_anomaly_detection_freshness_checks` to take advantage of a time series anomaly detection model to determine if data arrives later than expected.

<CodeExample filePath="guides/data-assets/quality-testing/freshness-checks/anomaly-detection.py" language="python" />

:::note
If the asset hasn't been updated enough times, the check will pass with a message indicating that more data is needed to detect anomalies.
:::

## Alerting on overdue assets

:::note
Freshness check alerts are a Dagster+ feature.
:::

In Dagster+, you can set up alerts to notify you when assets are overdue for an update. Refer to the [Dagster+ alerting guide](/dagster-plus/deployment/alerts) for more information.

## Next steps

- Explore more [asset checks](/guides/asset-checks)
- Explore how to [raise alerts when assets are overdue](/dagster-plus/deployment/alerts) (Dagster+ Pro)