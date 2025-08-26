---
title: Managing the project
description: Managing your dbt project
last_update:
  author: Dennis Hume
sidebar_position: 60
---

With most of the core integration logic in place, this last section covers some best practices tailored to this project, particularly around partitioning and managing dependencies in a hybrid Dagster and dbt pipeline.

## Handling multiple partitions

Both the `taxi_trips` asset and the dbt-generated assets are partitioned to represent slices of time. However, they don’t need to share the same partitioning scheme.

`taxi_trips` ingests files where each file represents one month of data. So, it makes sense for this asset to use a monthly partitioning strategy. The dbt models, on the other hand, can be executed more frequently, such as daily, to deliver fresher analytical outputs.

To support this, the codebase defines two separate partition definitions over the same time range:

- `monthly_partition` – used by the `taxi_trips` asset.
- `daily_partition` – used by `get_dbt_partitioned_models`.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/partitions.py"
  language="python"
  title="src/project_dbt/defs/partitions.py"
/>

This design gives you the flexibility to control data ingestion and transformation frequency independently, while still preserving upstream and downstream relationships between the assets.

You can observe this difference in the asset graph:

- `taxi_trips` references 3 partitions (e.g., 2024-05, 2024-06, 2024-07).
- dbt assets reference 90 partitions (one for each day across those 3 months).

![2048 resolution](/images/examples/dbt/asset_graph_partitions.png)

:::note

When executing Dagster assets, you can only materialize subsets of the asset graph that share the same partition definition. As a result, it's best to separate automation logic between ingestion and transformation layers—especially when they use different partition granularities.

:::

## Downstream assets

Earlier, we used a translator to align upstream Dagster assets (like `taxi_trips`) with the appropriate dbt sources (`trips`). This allowed us to maintain accurate lineage across boundaries.

If you want to define downstream assets that depend on dbt models, there’s no need to explicitly define those dbt assets yourself.

You can simply reference the appropriate asset key in your downstream asset definitions. This works because Dagster has already registered all dbt models as assets during parsing even though they weren't manually declared in your code.

This pattern allows for seamless integration across both hand-coded and dbt-derived assets.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/defs/assets/metrics.py"
  language="python"
  title="src/project_dbt/defs/assets/metrics.py"
/>

This will list all available Dagster asset keys, helping you verify model names, check dependencies, or debug execution plans.
