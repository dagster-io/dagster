---
description: Customize the behavior of components by creating a subclass of the component type.
sidebar_position: 400
title: Subclassing component types to customize behavior
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

You can customize the behavior of a component beyond what is available in the `component.yaml` file by creating a subclass of the component type.

There are two ways you can customize a component:

- For one-off customizations, you can create a _local_ component type, defined in a Python file in the same directory as your `component.yaml` file. Customarily, this local component type is defined in a file named `component.py` in the component directory.
- For customizations which may be reused across multiple components, you can create a _global_ component type, defined in a Python file in the `lib` directory. This requires that your project is a [`dg` plugin](./creating-dg-plugin) (projects scaffolded using the `dg` CLI are automatically plugins).

## Creating a customized component type

We'll use the `SlingReplicationCollectionComponent` as an example. First, we'll scaffold a project with the `dg` CLI:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/1-scaffold-project.txt" />
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/2-tree.txt" />

<Tabs>
<TabItem value="local" label="Local component type">

To define a local component type, you can create a subclass of your desired component in a file named `component.py` in the same directory as your `component.yaml` file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/3-component.py"
  language="python"
  title="my_project/defs/my_sling_sync/component.py"
/>

Next, update the `type` field in the `component.yaml` file to reference this new component type. It should be the fully qualified name of the type:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/5-component.yaml"
  language="yaml"
  title="my_project/defs/my_sling_sync/component.yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/4-tree.txt" />
</TabItem>
<TabItem value="global" label="Global component type">

To define a global component type, you can use the `dg` CLI to scaffold a new component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/3-scaffold-component-type.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/5-tree.txt" />

You can modify the generated component type by editing the `component.py` file in the `lib` directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/4-component.py"
  language="python"
  title="my_project/lib/custom_sling_replication_component.py"
/>

Finally, update the `type` field in the `component.yaml` file to reference the new component type:

<CodeExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/6-component.yaml" language="yaml" title="my_project/defs/my_sling_sync/component.yaml" />
</TabItem>
</Tabs>

Once you have created your component type subclass, you can customize its behavior by overriding methods from the parent class.

## Customizing execution

For components that define executable assets, it is customary for the component type to implement an `execute` method, which can be overridden to customize execution behavior.

For example, you can modify the custom subclass of `SlingReplicationCollectionComponent` to add a debug log message during execution:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/7-component.py"
  language="python"
/>

## Adding component-level templating scope

By default, the Jinja scopes available for use in a component's YAML file are:

- `env`: A function that allows you to access environment variables.
- `automation_condition`: A scope allowing you to access all static constructors of the `AutomationCondition` class.

It can be useful to add additional scope options to your component type. For example, you may have a custom automation condition that you'd like to use in your component.

To do so, you can define a function that returns an `AutomationCondition` and define a `get_additional_scope` method on your subclass:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/8-component.py"
  language="python"
/>

This can then be used in your `component.yaml` file:

<Tabs>
  <TabItem value="local" label="Local component type">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/9-component.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="global" label="Global component type">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/9-component.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>
