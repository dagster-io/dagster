---
title: Configuring runs via the UI
sidebar_label: Configuring assets via the UI
sidebar_position: 50
---

You will commonly want to manually materialize assets using the Dagster UI to backfill historical data, debug a production issue, or some other one-off task.

Often, you will want to be able to tweak some parameters when materializing these assets. This can be accomplished through the asset configuration system.

## What you'll learn

- How to add configuration to your assets
- How to modify the configuration when launching a run
- When to use asset configuration vs. [Resources](/docs/concepts/resources)

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/tutorial/quick-start) tutorial for an overview.
- Passing familiarity with [Pydantic](https://docs.pydantic.dev/latest/)
</details>

---

## Adding configuration to your asset

You must define a schema for the configuration you want to attach to your asset. For example, let's say we want to allow users to change a parallelism parameter for an asset:

<CodeExample filePath="guides/data-modeling/configuring-assets/config-schema.py" language="python" title="Adding configuration" />

## Modifying the configuration when launching a run

When launching a run using Dagster's Launchpad, you can provide a run config file as YAML or JSON that overrides the default configuration for your asset:

<CodeExample filePath="guides/data-modeling/configuring-assets/run_config.yaml" language="yaml" title="Run config provided via UI" />
