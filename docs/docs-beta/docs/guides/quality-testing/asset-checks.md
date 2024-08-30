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

The example below defines two asset checks using the `@multi_asset_check` decorator:

- One check that fails if the `order_id` column of the asset contains a null value
- Another check that fails if the `item_id` column of the asset contains a null value

In this example, both asset checks will run in a single operation after the asset has been materialized.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/multiple-asset-checks.py" language="python" title="Asset with multiple asset checks" />

## Programmatically generating asset checks

Defining multiple checks can also be done using a factory pattern. The example below defines the same two asset checks as in the previous example, but this time using a factory pattern and the `@multi_asset_check` decorator.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/asset-checks-factory.py" language="python" title="Defining asset checks using a factory pattern" />

## Blocking downstream assets

By default, if a parent's asset check fails during a run, the run will continue and downstream assets will be materialized. To prevent this behavior, set the `blocking` argument to `True` in the `@asset_check` decorator. This will cause the run to fail and prevent further materializations.

In the example bellow, when the `orders_id_has_no_nulls` check fails, the `augmented_orders` asset won't be materialized.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/block-downstream-with-asset-checks.py" language="python" title="Block downstream assets when asset check fails" />

## Scheduling and monitoring asset checks

In some cases, running asset checks separately from the job materializing the assets can be useful. For example, running all data quality checks once a day and sending an alert if they fail. This can be achieved using schedules and sensors.

In the example below, two jobs are defined: one for the asset and another for the asset check.

Using these jobs, schedules are defined to materialize the asset and execute the asset check independently. A sensor is defined to send an email alert when the asset check job fails.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/asset-checks-with-schedule-and-sensor.py" language="python" title="Schedule and monitor asset checks separately from their asset" />

## Next steps

- Learn more about assets in [Understanding Assets](/concepts/assets)
- Learn more about asset checks in [Understanding Asset Checks](/concepts/assets/asset-checks)
- Learn about how to use Great Expectations with Dagster in [our blog post](https://dagster.io/blog/ensuring-data-quality-with-dagster-and-great-expectations)