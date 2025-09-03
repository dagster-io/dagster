---
title: 'Using partitions'
sidebar_position: 250
description: Learn how to add and manage partitions when building pipelines with Dagster components.
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import CodeExample from '@site/src/components/CodeExample';

[Partitions](/guides/build/partitions-and-backfills/partitioning-assets) allow you to divide your assets into subsets based on time, categories, or other dimensions. When working with Dagster components, you can add partitions to your assets using either YAML configuration or Python code.

:::note Prerequisites

Before adding partitions to a component, you must either [create a components-ready Dagster project](/guides/build/projects/creating-a-new-project) or [migrate an existing project to `dg`](/guides/build/projects/moving-to-components/migrating-project).

:::

## Adding partitions in YAML

If you've defined your component using a `defs.yaml` file, you'll first want to define a new `template_var` that returns the `PartitionsDef` object. Create a `template_vars.py` file in the same directory as your component's `defs.yaml`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/partitions/template_vars.py"
  title="template_vars.py"
  language="python"
/>

From there, the simplest way to add a `PartitionsDefinition` to assets in a component is with the `post_processing` configuration in your `defs.yaml` file:

```yaml
type: ...
attributes: ...
template_vars_module: .template_vars
post_processing:
  assets:
    - target: "*"
      attributes:
        partitions_def: "{{ the_daily_partitions_def }}"
```

:::info

In general, it is best to avoid applying different partition definitions to different assets within a single component, since each execution step must map to only a single partitions definition at a time. Any integration that maps multiple assets to the same step must take care to ensure that all of those assets have the same partitions definition, which is easiest if all assets in the entire component share a single partitions definition.

:::

## Adding partitions in Python

If you are using the <PyObject section="components" module="dagster" object="component_instance" decorator /> decorator to define your component, you can create a subclass of your component class that applies partitions to all assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/partitions/python_partitions.py"
  title="Adding partitions with Python"
  language="python"
/>

## Updating your execution logic

Once you've added partitions to your assets, you'll need to update your asset execution logic to work with the partition context. When Dagster executes a partitioned asset, it provides information about which partition is currently being processed.

In your asset functions, you can access partition information through the <PyObject section="execution" module="dagster" object="AssetExecutionContext" />. The key properties are:
- <PyObject section="execution" module="dagster" object="AssetExecutionContext.partition_key" displayText="partition_key" />: The string key identifying the current partition.
- <PyObject section="execution" module="dagster" object="AssetExecutionContext.partition_time_window" displayText="partition_time_window" />: For time-based partitions, the start and end times for this partition.

Your execution logic should use this partition information to process only the relevant subset of data.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/partitions/partitioned_execution.py"
  title="Partitioned execution example"
  language="python"
/>

## Best practices

- **Use consistent partitions**: All assets within a single component should generally use the same partitions definition to avoid execution complexity.
- **Handle partition context**: Always use `AssetExecutionContext.partition_key` or related methods to access partition information in your execution logic.
- **Test partitioned assets**: Ensure your partitioned assets work correctly by testing with different partition keys during development.