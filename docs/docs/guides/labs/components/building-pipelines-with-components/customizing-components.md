---
title: 'Customizing components'
sidebar_position: 400
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

You can customize the behavior of a component beyond what is available in the `component.yaml` file.

To do so, you can create a subclass of your desired component in a file named `component.py` in the same directory as your `component.yaml` file. This subclass should be annotated with the `@component_type` decorator, which will define a local name for this component:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/custom-subclass/basic-subclass.py" language="python" />

You can then update the `type:` field in your `component.yaml` file to reference this new component type. The new type name will be `.<component-name>`, where the leading `.` indicates that this is a local component type:

```yaml
type: .custom_subclass

attributes:
    ...
```

## Customizing execution

By convention, most library components have an `execute()` method that defines the core runtime behavior of the component. This can be overridden by subclasses of the component to customize this behavior.

For example, we can create a subclass of the `SlingReplicationCollectionComponent` that adds a debug log message during execution:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/custom-subclass/debug-mode.py" language="python" />

## Adding component-level templating scope

By default, the scopes available for use in the template are:

- `env`: A function that allows you to access environment variables.
- `automation_condition`: A scope allowing you to access all static constructors of the `AutomationCondition` class.

However, it can be useful to add additional scope options to your component type. For example, you may have a custom automation condition that you'd like to use in your component.

To do so, you can define a function that returns an `AutomationCondition` and define a `get_additional_scope` method on your subclass:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/custom-subclass/custom-scope.py" language="python" />

This can then be used in your `component.yaml` file:

```yaml
component_type: .custom_subclass

attributes:
    ...
    transforms:
        - attributes:
            automation_condition: "{{ custom_cron('@daily') }}"
```
