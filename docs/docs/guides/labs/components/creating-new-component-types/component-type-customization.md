---
title: Advanced component type customization
description: Advanced customization for component types you have created.
sidebar_position: 200
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

## Prerequisites

Before following the steps below, you will need to [create and register a component type](/guides/labs/components/creating-new-component-types/creating-and-registering-a-component-type).

## Customizing scaffolding behavior

By default, when you instantiate a component type, `dg scaffold` will create a new directory alongside an unpopulated `defs.yaml` file. However, you can customize this behavior by decorating your component type with `@scaffold_with`.

In the example below, the custom `ShellCommandScaffolder` class scaffolds a template shell script alongside a populated `defs.yaml` file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-scaffolder.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

Now, when you run `dg scaffold`, you should see a template shell script created along with a populated `defs.yaml` file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/5-scaffolded-defs.yaml"
  language="yaml"
  title="my_component_library/components/my_shell_command/defs.yaml"
/>

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/6-scaffolded-component-script.sh"
  language="bash"
  title="my_component_library/components/my_shell_command/script.sh"
/>

## Providing resolution logic for non-standard types

In most cases, the types you use in your component schema and in the component class will be the same, or will have out-of-the-box resolution logic, as in the case of `ResolvedAssetSpec`.

However, in some cases, you may want to use a type that doesn't have an existing schema equivalent. In that case, you can provide a function that will resolve the value to the desired type by providing an annotation on the field with `Annotated[<type>, Resolver(...)]`.

For example, to provide an API client to a component, which can be configured with an API key in YAML, or a mock client in tests, you would do the following:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/custom-schema-resolution.py"
  language="python"
/>

## Customizing rendering of YAML values

The components system supports a rich templating syntax that allows you to load arbitrary Python values based off of your `defs.yaml` file. All string values in a `Resolvable` can be templated using the Jinja2 templating engine, and may be resolved into arbitrary Python types. This allows you to expose complex object types, such as `PartitionsDefinition` or `AutomationCondition` to users of your component, even if they're working in pure YAML.

You can define custom values that will be made available to the templating engine by defining a `get_additional_scope` classmethod on your component. In our case, we can define a `"daily_partitions"` function which returns a `DailyPartitionsDefinition` object with a pre-defined start date:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-custom-scope.py"
  language="python"
/>

When a user instantiates this component, they will be able to use this custom scope in their `defs.yaml` file:

```yaml
component_type: my_component

attributes:
  script_path: script.sh
  asset_specs:
    - key: a
      partitions_def: '{{ daily_partitions }}'
```
