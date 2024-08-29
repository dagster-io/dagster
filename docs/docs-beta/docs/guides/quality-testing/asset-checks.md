---
title: "Test assets with Asset Checks"
sidebar_position: 10
---

Asset checks in Dagster provide a way to define and execute different types of data quality checks on your data assets directly in Dagster.

This guide covers the most common use cases for testing assets with asset checks and taking action based on the result.

<details>
<summary>Prerequisites</summary>
- Familiarity with [Assets](/concepts/assets)
</details>

## Testing assets with a single asset check

The example below defines a single asset check on an asset that fails if the `order_id` column of the asset contains a null value.

In this example, the asset check will run after the asset has been materialized, to ensure the quality of its data.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/single-asset-check.py" language="python" title="Asset with a single asset check" />

## Testing assets with multiple asset checks

In most cases, checking the data quality of an asset will require multiple checks.

The example below defines two asset checks on an asset using the `multi_asset_check` decorator.
- one that fails if the `order_id` column of the asset contains a null value.
- another one that fails if the `item_id` column of the asset contains a null value.

In this example, both asset check will run in a single operation after the asset has been materialized.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/multiple-asset-checks.py" language="python" title="Asset with multiple asset checks" />

## Blocking downstream assets

By default, materialization of downstream assets will continue, even if a parent's asset check fails. To block the materialization of downstream assets, set the `blocking` argument to `True` in the `asset_check` decorator.

In the example bellow, when the `orders_id_has_no_nulls` check fails, the `augmented_orders` asset isn't materialized.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/block-downstream-with-asset-checks.py" language="python" title="Block downstream assets when asset check fails" />

## Executing asset checks on a schedule

In some case, it may be useful to run the asset checks on a schedule, separately from the job materializing the assets.

In the example below, two jobs are defined, one for the asset and another one for the asset check. Using these jobs, schedules are defined to materialize the asset and execute the asset check independently.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/asset-checks-with-schedule.py" language="python" title="Schedule asset checks separately from their asset" />

## Next steps

- Learn more about assets in [Understanding Assets](/concepts/assets)
- Learn more about asset checks in [Understanding Asset Checks](/concepts/assets/asset-checks)
- Learn about how to use Great Expectations with Dagster in [our blog post](https://dagster.io/blog/ensuring-data-quality-with-dagster-and-great-expectations)