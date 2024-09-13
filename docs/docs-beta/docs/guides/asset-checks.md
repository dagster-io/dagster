---
title: "Testing assets with Asset Checks"
sidebar_position: 10
sidebar_label: "Asset Checks"
---

Asset checks in Dagster provide a way to define and execute different types of data quality checks on your data assets.

This guide covers the most common use cases for testing assets with asset checks and taking action based on the result.

<details>
<summary>Prerequisites</summary>

To follow this guide, you'll need:

- Familiarity with [Assets](/concepts/assets)
</details>

## Defining a single asset check \{#single-check}

:::tip
Dagster's dbt integration can model existing dbt tests as asset checks. Refer to the [dagster-dbt documentaiton](/integrations/dbt) for more information.
:::

Single asset checks are defined using the `@asset_check` decorator.

The following example defines an asset check on an asset that fails if the `order_id` column of the asset contains a null value. The asset check will run after the asset has been materialized, to ensure the quality of its data.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/single-asset-check.py" language="python" />

## Defining multiple asset checks \{#multiple-checks}

In most cases, checking the data quality of an asset will require multiple checks.

The following example defines two asset checks using the `@multi_asset_check` decorator:

- One check that fails if the `order_id` column of the asset contains a null value
- Another check that fails if the `item_id` column of the asset contains a null value

In this example, both asset checks will run in a single operation after the asset has been materialized.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/multiple-asset-checks.py" language="python" />

## Programmatically generating asset checks \{#factory-pattern}

Defining multiple checks can also be done using a factory pattern. The example below defines the same two asset checks as in the previous example, but this time using a factory pattern and the `@multi_asset_check` decorator.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/asset-checks-factory.py" language="python" />

## Blocking downstream materialization

:::info
This feature is only supported by the `@asset_check` decorator.
:::

By default, if a parent's asset check fails during a run, the run will continue and downstream assets will be materialized. To prevent this behavior, set the `blocking` argument to `True` in the `@asset_check` decorator.

In the example bellow, if the `orders_id_has_no_nulls` check fails, the downstream `augmented_orders` asset won't be materialized.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/block-downstream-with-asset-checks.py" language="python" />

## Scheduling and monitoring asset checks

In some cases, running asset checks separately from the job materializing the assets can be useful. For example, running all data quality checks once a day and sending an alert if they fail. This can be achieved using schedules and sensors.

In the example below, two jobs are defined: one for the asset and another for the asset check. Schedules are defined to materialize the asset and execute the asset check independently. A sensor is defined to send an email alert when the asset check job fails.

<CodeExample filePath="guides/data-assets/quality-testing/asset-checks/asset-checks-with-schedule-and-sensor.py" language="python" />

## Next steps

- Learn more about assets in [Understanding Assets](/concepts/assets)
- Learn more about asset checks in [Understanding Asset Checks](/concepts/assets/asset-checks)
- Learn how to use [Great Expectations with Dagster](https://dagster.io/blog/ensuring-data-quality-with-dagster-and-great-expectations)