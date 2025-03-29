---
title: 'Customizing components'
sidebar_position: 400
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

You can customize the behavior of a component beyond what is available in the `component.yaml` file.

To do so, you can create a subclass of your desired component in a file named `component.py` in the same directory as your `component.yaml` file.

<CodeExample path="docs_snippets/docs_snippets/guides/components/custom-subclass/basic-subclass.py" language="python" />

You can then update the `type:` field in your `component.yaml` file to reference this new component type. It should be the fully qualified name of the type.

```yaml
type: my_project.defs.my_def.CustomSubclass

attributes: ...
```

## Customizing execution

For example, we can create a subclass of the `SlingReplicationCollectionComponent` that adds a debug log message during execution. `SlingReplicationCollectionComponent` has an `execute` method that can be overriden by subclasses.

<CodeExample path="docs_snippets/docs_snippets/guides/components/custom-subclass/debug-mode.py" language="python" />

## Adding component-level templating scope

By default, the scopes available for use in the template are:

- `env`: A function that allows you to access environment variables.
- `automation_condition`: A scope allowing you to access all static constructors of the `AutomationCondition` class.

However, it can be useful to add additional scope options to your component type. For example, you may have a custom automation condition that you'd like to use in your component.

To do so, you can define a function that returns an `AutomationCondition` and define a `get_additional_scope` method on your subclass:

<CodeExample path="docs_snippets/docs_snippets/guides/components/custom-subclass/custom-scope.py" language="python" />

This can then be used in your `component.yaml` file:

```yaml
type: my_project.defs.my_def.CustomSubclass

attributes:
    ...
    asset_post_processors:
        - attributes:
            automation_condition: "{{ custom_cron('@daily') }}"
```
