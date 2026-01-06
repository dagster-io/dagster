---
description: Learn how to combine Dagster Components with traditional Pythonic asset definitions in a single project.
sidebar_position: 400
title: Combining Components with Pythonic definitions
---

As your Dagster project grows, you may want to leverage [Components](/guides/build/components) for standardized data pipelines while still maintaining traditional <PyObject section="assets" module="dagster" object="asset" decorator /> definitions for custom logic. This guide shows how to combine both approaches in a single project using `Definitions.merge`.

## When to use this pattern

This pattern is useful when you:

- Want to use Components for standardized integrations (Sling, dbt, etc.) but need custom Python logic for specific transformations
- Are migrating an existing project to Components incrementally
- Have team members who prefer working with Python code while others benefit from Components' declarative approach

## Example project structure

Here's a project that combines Components with traditional Pythonic assets:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/combining-components-with-pythonic-defs/1-tree.txt" />

This structure includes:

| Directory | Purpose |
|-----------|---------|
| `defs/` | Contains Dagster Components (Sling, dbt, etc.) that are auto-loaded |
| `assets/` | Traditional `@asset` definitions written in Python |
| `resources/` | Shared resources used by both Components and Pythonic assets |

## Combining definitions

The key to combining Components with Pythonic assets is using `Definitions.merge`. This merges multiple `Definitions` objects together:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/combining-components-with-pythonic-defs/component_defs.py"
  startAfter="start_definitions_simple"
  endBefore="end_definitions_simple"
  title="my_project/src/my_project/definitions.py"
/>

This pattern:
1. Uses `load_from_defs_folder` to automatically discover and load Components from the `defs/` folder
2. Creates a separate `Definitions` object for your Pythonic assets
3. Merges them together using `Definitions.merge`

## Sharing resources across both types

When Components and Pythonic assets need to share resources (like a database connection), you can bind resources when creating your definitions.

There are two recommended patterns for organizing resources:

<Tabs>
<TabItem value="pattern1" label="Pattern 1: resources/ module">

Keep resources in a `resources/` Python module and bind them in `definitions.py`. This pattern is best for:
- Complex resource logic that benefits from being in a dedicated module
- Resources that need unit testing
- Sharing resources across multiple code locations

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/combining-components-with-pythonic-defs/component_defs.py"
  startAfter="start_resources"
  endBefore="end_resources"
  title="my_project/src/my_project/resources/__init__.py"
/>

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/combining-components-with-pythonic-defs/component_defs.py"
  startAfter="start_definitions_with_resources"
  endBefore="end_definitions_with_resources"
  title="my_project/src/my_project/definitions.py"
/>

</TabItem>
<TabItem value="pattern2" label="Pattern 2: defs/ folder">

Define resources in a `defs.py` file inside the `defs/` folder. This pattern is best for:
- Simple resources with minimal configuration
- Component-centric architectures
- Resources that are primarily used by Components

```
my_project/src/my_project/
└── defs/
    ├── shared_resources/
    │   └── defs.py      # Returns Definitions with resources
    ├── raw_data_sync/
    │   └── defs.yaml
    └── analytics_dbt/
        └── defs.yaml
```

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/combining-components-with-pythonic-defs/component_defs.py"
  startAfter="start_resources_in_defs"
  endBefore="end_resources_in_defs"
  title="my_project/src/my_project/defs/shared_resources/defs.py"
/>

Resources defined this way are automatically discovered by `load_from_defs_folder`.

</TabItem>
</Tabs>

Your traditional `@asset` functions can request resources by parameter name:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/combining-components-with-pythonic-defs/component_defs.py"
  startAfter="start_assets"
  endBefore="end_assets"
  title="my_project/src/my_project/assets/analytics.py"
/>

The resource key (`warehouse`) in the `resources` dict matches the parameter name in the asset functions, allowing Dagster to inject the resource automatically.

### Where resources should NOT live

Avoid these patterns when organizing resources:

| ❌ Anti-pattern | Why it's problematic |
|----------------|---------------------|
| `defs/snowflake/defs.yaml` | Resources are not Components. Components produce assets; resources are dependencies. YAML component definitions require a Component class. |
| `resource/snowflake/` (singular) | Inconsistent naming and unnecessary nesting. Use `resources/` (plural) as a flat module. |

## Best practices

When combining Components with Pythonic definitions:

- **Use Components for standardized integrations**: Sling for data replication, dbt for transformations, etc.
- **Use Pythonic assets for custom logic**: Complex transformations, ML models, or business logic that doesn't fit a Component
- **Share resources through `definitions.py`**: Bind resources at the top level so they're available to all assets
- **Keep resource logic in a `resources/` module**: Makes resources testable and reusable

## Next steps

- Learn how to [add Components to an existing project](/guides/build/projects/moving-to-components/adding-components-to-existing-project)
- Explore [available Components](/guides/build/components)
- Read about [creating custom Components](/guides/build/components/creating-new-components)
