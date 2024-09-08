---
title: Configuring assets using the Dagster UI
sidebar_label: Configure asset runs
sidebar_position: 50
---

You will commonly want to manually materialize assets using the Dagster UI to backfill historical data, debug a production issue, or some other one-off task.

Often, you will want to be able to tweak some parameters when materializing these assets. This can be accomplished through the asset configuration system.

## What you'll learn

- How to make your assets configurable
- How to provide configuration when launching a run

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/getting-started/quickstart) tutorial for an overview.
- Familiarity with [Pydantic](https://docs.pydantic.dev/latest/)
- An understanding of [Ops vs Assets](/concepts/ops-jobs/ops-vs-assets)
</details>

---

## Making assets configurable

For an asset to be configurable, you must first define a schema that inherits from the Dagster `Config` class. For example, let's say we want to allow users to change the lookback time window for the computation that materializes an asset:

<CodeExample filePath="guides/data-modeling/configuring-assets/config-schema.py" language="python" title="Adding configuration" />

## Providing configuration when launching a run

When launching a run using Dagster's Launchpad, you can provide a run config file as YAML or JSON that overrides the default configuration for your asset:

<CodeExample filePath="guides/data-modeling/configuring-assets/run_config.yaml" language="yaml" title="Run config provided via UI" />

Run configurations reference an `op` which is the underlying compute associated with an asset. See [the Ops vs Assets](/concepts/ops-jobs/ops-vs-assets) documentation for more information.
