---
title: "Testing assets with Asset checks"
sidebar_position: 10
sidebar_label: "Asset checks"
---

Asset checks are tests that verify specific properties of your data assets, allowing you to execute data quality checks on your data. For example, you can create checks to:

- Ensure a particular column doesn't contain null values
- Verify that a tabular asset adheres to a specified schema
- Check if an asset's data needs refreshing

Each asset check should test only a single asset property to keep tests uncomplicated, reusable, and easy to track over time.

<details>
<summary>Prerequisites</summary>

To follow this guide, you'll need:

- Familiarity with [Assets](/concepts/assets)
</details>

## Getting started

To get started with asset checks, follow these general steps:

1. **Define an asset check:** Asset checks are typically defined using the `@asset_check` or `@multi_asset_check` decorator and run either within an asset or separate from the asset.
2. **Pass the asset checks to the `Definitions` object:** Asset checks must be added to `Definitions` for Dagster to recognize them.
3. **Choose how to execute asset checks**: By default, all jobs targeting an asset will also run associated checks, although you can run asset checks through the Dagster UI.
4. **View asset check results in the UI**: Asset check results will appear in the UI and can be customized through the use of metadata and severity levels
5. **Alert on failed asset check results**: If you are using Dagster+, you can choose to alert on asset checks.

## Defining a single asset check \{#single-check}

:::tip
Dagster's dbt integration can model existing dbt tests as asset checks. Refer to the [dagster-dbt documentaiton](/integrations/dbt) for more information.
:::

A asset check is defined using the `@asset_check` decorator.

The following example defines an asset check on an asset that fails if the `order_id` column of the asset contains a null value. The asset check will run after the asset has been materialized.

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
