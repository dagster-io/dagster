---
title: Configuring assets and ops via the UI
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
