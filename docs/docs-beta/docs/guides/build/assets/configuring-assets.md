---
title: Configuring assets in the UI
sidebar_position: 600
---

The Dagster UI is commonly used to manually materialize assets, backfill historical data, debug a production issue, or some other one-off task.

You'll often want to be able to adjust parameters when materializing assets, which can be accomplished with Dagster's asset configuration system.

:::note

This article assume familiarity with [assets](/guides/build/assets/defining-assets) and [Pydantic](https://docs.pydantic.dev/latest/).

:::


## Making assets configurable

For an asset to be configurable, first define a schema that inherits from the Dagster `Config` class.

For example, you want to allow your team to change the lookback time window for the computation that materializes an asset:

<CodeExample filePath="guides/data-modeling/configuring-assets/config-schema.py" language="python" />

## Specifying config using the Dagster UI

:::note
Run configurations reference an `op` which is the underlying compute associated with an asset.
:::

When launching a run using the Launchpad in the UI, you can provide a run config file as YAML or JSON that overrides the default configuration for your asset.

On any page with a **Materialize** button, click the **options menu > Open launchpad** to access the Launchpad:

![Highlighted Open Launchpad option in the Materialize options menu of the Dagster UI](/img/placeholder.svg)

This will open the Launchpad, where you can scaffold the config, customize its values, and manually materialize the asset:

![Dagster Launchpad that configures an asset to have a lookback window of 7 days](/img/placeholder.svg)

## Next steps

- Learn more about Dagster [assets](/guides/build/assets/)
- Connect to external [APIs](/guides/build/external-resources/connecting-to-apis) and [databases](/guides/build/external-resources/connecting-to-databases) with resources
