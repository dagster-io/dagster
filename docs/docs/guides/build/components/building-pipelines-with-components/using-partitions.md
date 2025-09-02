---
title: 'Using partitions'
sidebar_position: 250
description: Learn how to add and manage partitions when building pipelines with Dagster components.
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import CodeExample from '@site/src/components/CodeExample';

Partitions allow you to divide your assets into subsets based on time, categories, or other dimensions. When working with Dagster components, you can add partitions to your assets using either YAML configuration or Python code.

:::note Prerequisites

Before adding partitions to a component, you must either [create a components-ready Dagster project](/guides/build/projects/creating-a-new-project) or [migrate an existing project to `dg`](/guides/build/projects/moving-to-components/migrating-project).

:::

## Adding partitions in YAML

If you've defined your component using a `defs.yaml` file, you'll first want to define a new `template_var` that returns the `PartitionsDef` object:

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

In the above snippet, we're applying the same `partitions_def` to all assets within the component. In general, it is recommended to avoid applying different partition definitions to different assets within a single component because each execution step must map to only a single partitions definition at a time. Any integration that maps multiple assets to the same step must take care to ensure that all of those assets have the same partitions definition, which is easiest if all assets in the entire component share a single partitions definition.

## Adding partitions in Python

If you are using the `@component_instance` decorator to define your component, the simplest path will often be to create a new subclass of your component class. For example, you would transform:

```python
import dagster as dg

@dg.component_instance
def the_component():
    return SomeComponent()
```

into:

```python
import dagster as dg

def add_partitions_def(spec: dg.AssetSpec) -> dg.AssetSpec:
    return spec.replace_attributes(
        partitions_def=dg.DailyPartitionsDefinition(start_date="2020-01-01")
    )

class SomeComponentWithPartitions(SomeComponent):
    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        # Use map_asset_specs to add a property to all assets
        return super().build_defs(context).map_asset_specs(
            add_partitions_def
        )
        
        
@dg.component_instance
def the_component():
    return SomeComponentWithPartitions()
```

## Updating your execution logic

If you intend to materialize the assets that you've defined, you'll generally need to update your execution function to handle the new partitions definition. This can be done by creating a subclass of your component definition. The specifics of how you do this depend on the details of how the asset is being executed.

The general strategy is to look at the `AssetExecutionContext.partition_key` (which is the partition key that is intended to be executed for the current execution), and change the code that you're running based on its value. For example, you might have code that only computes data for the range of time defined by that key.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/partitions/partitioned_execution.py"
  title="Partitioned execution example"
  language="python"
/>

## Best practices

- **Use consistent partitions**: All assets within a single component should generally use the same partitions definition to avoid execution complexity.
- **Handle partition context**: Always use `AssetExecutionContext.partition_key` or related methods to access partition information in your execution logic.
- **Test partitioned assets**: Ensure your partitioned assets work correctly by testing with different partition keys during development.