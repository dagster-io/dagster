---
title: "Adding a component to a project"
sidebar_position: 100
unlisted: true
---


## Finding a component

You can view the available component types in your environment by running the following command:

```bash
dg component-type list
```

This will display a list of all the component types that are available in your project. If you'd like to see more information about a specific component, you can run:

```bash
dg component-type docs <component-name>
```

This will display a webpage containing documentation for the specified component type.

## Scaffolding a component

Once you've selected the component type that you'd like to use, you can instantiate a new component by running:

```bash
dg component generate <component-type> <component-name>
```

This will create a new directory underneath your `components/` folder that contains a `component.yaml` file. Some components may also generate additional files as needed.

## Basic configuration

The `component.yaml` is the primary configuration file for a component. It contains two top-level fields:

- `type`: The type of the component defined in this directory
- `params`: A dictionary of parameters that are specific to this component type. The schema for these params is defined by the `get_schema` method on the component class.

To see a sample `component.yaml` file for your specific component, you can run:

```bash
dg component-type docs <component-name>
```

## Component templating

Each `component.yaml` file supports a rich templating syntax, powered by `jinja2`.

### Templating environment variables

A common use case for templating is to avoid exposing environment variables (particularly secrets) in your yaml files. The Jinja scope for a `component.yaml` file contains an `env` function which can be used to insert environment variables into the template.

```yaml
component_type: my_snowflake_component

params:
    account: {{ env('SNOWFLAKE_ACCOUNT') }}
    password: {{ env('SNOWFLAKE_PASSWORD') }}
```

## Customizing a component

Sometimes, you may want to customize the behavior of a component beyond what is available in the `component.yaml` file.

To do this, you can create a subclass of your desired component in the same directory as your `component.yaml` file. By convention, this subclass should be created in a file named `component.py`.

This subclass should be annotated with the `@component_type` decorator, which will define a local name for this component:


<CodeExample filePath="guides/components/custom-subclass/basic-subclass.py" language="python" />

You can then update the `type:` field in your `component.yaml` file to reference this new component type. The new type name will be `.<component-name>`, where the leading `.` indicates that this is a local component type.

```yaml
type: .custom_subclass

params:
    ...
```

### Customizing execution

By convention, most library components have an `execute()` method that defines the core runtime behavior of the component. This can be overridden by subclasses of the component to customize this behavior.

For example, we can create a subclass of the `SlingReplicationCollectionComponent` that adds a debug log message during execution:

<CodeExample filePath="guides/components/custom-subclass/debug-mode.py" language="python" />


### Adding component-level templating scope

By default, the scopes available for use in the template are:

- `env`: A function that allows you to access environment variables.
- `automation_condition`: A scope allowing you to access all static constructors of the `AutomationCondition` class.

However, it can be useful to add additional scope options to your component type. For example, you may have a custom automation condition that you'd like to use in your component.

To do so, you can define a function that returns an `AutomationCondition` and define a `get_additional_scope` method on your subclass:

<CodeExample filePath="guides/components/custom-subclass/custom-scope.py" language="python" />

This can then be used in your `component.yaml` file:

```yaml
component_type: .custom_subclass

params:
    ...
    transforms:
        - attributes:
            automation_condition: "{{ custom_cron('@daily') }}"
```