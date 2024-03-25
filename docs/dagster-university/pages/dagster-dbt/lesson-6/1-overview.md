---
title: 'Lesson 6: Overview'
module: 'dagster_dbt'
lesson: '6'
---

# Overview

By default, dbt materializes tables by replacing the old table with the new one generated from the model. However, there are many situations where you’ll want to append new data to existing data without replacing it. dbt provides an `incremental` materialization pattern for this. Incremental materialization allows developers to define when the data was transformed and only transform data that hasn’t already been transformed.

In some situations, a normal incremental model might be brittle. This might be because:

1. **Incremental runs aren’t repeatable**. By this, we mean materializing an incremental model twice does two different things and those states cannot be easily replicated. One run might add 10 million rows, and immediately running it again might not add any rows at all. Incremental models are also difficult to roll back changes because the boundaries of what rows to insert are dynamic and not tracked by dbt.
2. **Re-running historical data requires you to re-run everything with a `full refresh`**. If you find out that the data from three incremental materializations ago used incorrect source data, and then the source data was corrected, you’ll have to rebuild your *entire* incremental model from scratch. This is problematic because incremental models are typically used for large and expensive tables. Therefore, doing a full rebuild is a long and costly process.

All this said, incremental models aren’t *bad*. They could just be better. Incremental models would be better if they could be made predictably repeatable and didn’t require rebuilding an entire table if one portion was wrong.

---

## Dagster partitions can help

{% callout %}
> 💡 **Need a primer on partitions?** Check this [Dagster Short](https://www.youtube.com/watch?v=zfLBHFCbocE) on YouTube!
{% /callout %}

Dagster partitions are predictable, repeatable, and don’t require a massive rebuild when one chunk of data is incorrect. A partition has discrete bounds, such as partitioning an asset by month or location, making it easy to understand what data will be created each time a partition is materialized. 

Partitions can also be run independently from each other. If only one partition went awry, then you can re-materialize just that single erroneous partition without remaking your entire asset.

In this lesson, we’re going to write an incremental dbt model and make it easier to manage by partitioning it.