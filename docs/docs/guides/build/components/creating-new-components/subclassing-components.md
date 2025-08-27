---
description: Customize the behavior of components by creating a subclass of the component.
sidebar_position: 400
title: Subclassing components to customize behavior
---

You can customize the behavior of a component beyond what is available in the `defs.yaml` file by creating a subclass of the component.

{/* There are two ways you can customize a component: */}

{/* - For one-off customizations, you can create a _local_ component, defined in a Python file in the same directory as your `defs.yaml` file. Customarily, this local component is defined in a file named `component.py` in the component directory. */}
{/* - For customizations which may be reused across multiple components, you can create a _global_ component, defined in a Python file in the `components` directory. This requires that your project is a [`dg` plugin](./creating-dg-plugin) (projects scaffolded using the `dg` CLI are automatically plugins). */}

## Creating a customized component

We'll use the `SlingReplicationCollectionComponent` as an example. First, we'll scaffold a project with the `dg` CLI:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/1-scaffold-project.txt" />
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/2-tree.txt" />

<Tabs>
<TabItem value="local" label="Local component">

To define a local component, you can create a subclass of your desired component in a file named `component.py` in the same directory as your `defs.yaml` file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/3-component.py"
  language="python"
  title="my_project/defs/my_sling_sync/component.py"
/>

Next, update the `type` field in the `defs.yaml` file to reference this new component. It should be the fully qualified name of the type:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/5-defs.yaml"
  language="yaml"
  title="my_project/defs/my_sling_sync/defs.yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/4-tree.txt" />
</TabItem>
<TabItem value="global" label="Global component">

To define a global component, you can use the `dg` CLI to scaffold a new component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/3-scaffold-component.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/5-tree.txt" />

You can modify the generated component by editing the `component.py` file in the `components` directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/4-component.py"
  language="python"
  title="my_project/components/custom_sling_replication_component.py"
/>

Finally, update the `type` field in the `defs.yaml` file to reference the new component:

<CodeExample path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/6-defs.yaml" language="yaml" title="my_project/defs/my_sling_sync/defs.yaml" />
</TabItem>
</Tabs>

Once you have created your component subclass, you can customize its behavior by overriding methods from the parent class.

## Customizing execution

For components that define executable assets, it is customary for the component to implement an `execute` method, which can be overridden to customize execution behavior.

For example, you can modify the custom subclass of `SlingReplicationCollectionComponent` to add a debug log message during execution:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/7-component.py"
  language="python"
/>

## Adding component-level templating scope

By default, the Jinja scopes available for use in a component's YAML file are:

- `env`: A function that allows you to access environment variables.
- `automation_condition`: A scope allowing you to access all static constructors of the `AutomationCondition` class.

It can be useful to add additional scope options to your component. For example, you may have a custom automation condition that you'd like to use in your component.

To do so, you can define a function that returns an `AutomationCondition` and define a `get_additional_scope` method on your subclass:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/8-component.py"
  language="python"
/>

This can then be used in your `defs.yaml` file:

<Tabs>
  <TabItem value="local" label="Local component">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/local/9-defs.yaml"
      language="yaml"
    />
  </TabItem>
  <TabItem value="global" label="Global component">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/customizing-existing-component/global/9-defs.yaml"
      language="yaml"
    />
  </TabItem>
</Tabs>
