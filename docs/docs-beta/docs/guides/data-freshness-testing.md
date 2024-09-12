---
title: "Check for data freshness"
sidebar_position: 20
---
Freshness checks provide a way to identify data assets that are overdue for an update.

This guide covers how to construct freshness checks for materializable [assets](/todo) and [external assets](/todo).

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with [assets](/todo)
- Familiarity with [asset checks](/todo)

</details>

## Check data freshness for materializable assets

The example below defines a freshness check on an asset that fails if the asset's latest materialization occurred more than one hour before the current time.

Defining a schedule or sensor is required to ensure the freshness check executes. If the check only runs after the asset has been materialized, the check won't be able to detect the times materialization fails.

<CodeExample filePath="guides/data-assets/quality-testing/freshness-checks/materializable-asset-freshness-check.py" language="python" title="Check data freshness for materializable assets" />

## Check data freshness for external assets

To run freshness checks on external assets, the checks need to know when the external assets were last updated. Emitting these update timestamps as values for the [`dagster/last_updated_timestamp`](/todo) observation metadata key allows Dagster to calculate whether the asset is overdue.

The example below defines a freshness check and adds a schedule to run the check periodically.

<CodeExample filePath="guides/data-assets/quality-testing/freshness-checks/external-asset-freshness-check.py" language="python" title="Check data freshness for external assets" />

### Use anomaly detection to test data freshness (Dagster+ Pro)

Instead of applying policies on an asset-by-asset basis, Dagster+ Pro users can take advantage of a time series anomaly detection model to determine if data is arriving later than expected.

<CodeExample filePath="guides/data-assets/quality-testing/freshness-checks/anomaly-detection.py" language="python" title="Use anomaly detection to detect overdue assets" />

:::note
If the asset hasn't been updated enough times, the check will pass with a message indicating that more data is needed to detect anomalies.
:::

## Next steps

- Explore more [asset checks](/todo)
- Explore how to [raise alerts when assets are overdue](/todo) (Dagster+ Pro)
- Explore more about [anomaly detection](/todo) (Dagster+ Pro)
