---
title: "Run configuration"
description: Job run configuration allows providing parameters to jobs at the time they're executed.
sidebar_position: 100
---

Run configuration allows providing parameters to jobs at the time they're executed.

It's often useful to provide user-chosen values to Dagster jobs or asset definitions at runtime. For example, you might want to provide a connection URL for a database resource. Dagster exposes this functionality through a configuration API.

Various Dagster entities (assets, ops, resources) can be individually configured. When launching a job that materializes (assets), executes (ops), or instantiates (resources) a configurable entity, you can provide _run configuration_ for each entity. Within the function that defines the entity, you can access the passed-in configuration through the `config` parameter. Typically, the provided run configuration values correspond to a _configuration schema_ attached to the asset/op/resource definition. Dagster validates the run configuration against the schema and proceeds only if validation is successful.

A common use of configuration is for a [schedule](/guides/automate/schedules/) or [sensor](/guides/automate/sensors/) to provide configuration to the job run it is launching. For example, a daily schedule might provide the day it's running on to one of the assets as a config value, and that asset might use that config value to decide what day's data to read.

## Defining and accessing configuration

Configurable parameters accepted by an asset or op are specified by defining a config model subclass of <PyObject section="config" module="dagster" object="Config"/> and a `config` parameter to the corresponding asset or op function. Under the hood, these config models utilize [Pydantic](https://docs.pydantic.dev/), a popular Python library for data validation and serialization.

During execution, the specified config is accessed within the body of the op or asset using the `config` parameter.

<Tabs persistentKey="assetsorops">
<TabItem value="Using software-defined-assets">

Here, we define a subclass of <PyObject section="config" module="dagster" object="Config"/> holding a single string value representing the name of a user. We can access the config through the `config` parameter in the asset body.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_basic_asset_config" endBefore="end_basic_asset_config" />

</TabItem>
<TabItem value="Using ops and jobs">

Here, we define a subclass of <PyObject section="config" module="dagster" object="Config"/> holding a single string value representing the name of a user. We can access the config through the `config` parameter in the op body.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_basic_op_config" endBefore="end_basic_op_config" />

You can also build config into jobs.

</TabItem>
</Tabs>

These examples showcase the most basic config types that can be used. For more information on the set of config types Dagster supports, see [the advanced config types documentation](advanced-config-types).

## Defining and accessing Pythonic configuration for a resource

Configurable parameters for a resource are defined by specifying attributes for a resource class, which subclasses <PyObject section="resources" module="dagster" object="ConfigurableResource"/>. The below resource defines a configurable connection URL, which can be accessed in any methods defined on the resource.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_basic_resource_config" endBefore="end_basic_resource_config" />

For more information on using resources, refer to the [Resources guide](/guides/build/external-resources/).

## Specifying runtime configuration

To execute a job or materialize an asset that specifies config, you'll need to provide values for its parameters. How we provide these values depends on the interface we are using: Python, the Dagster UI, or the command line (CLI).

<Tabs persistentKey="configtype">
<TabItem value="Python">

When specifying config from the Python API, we can use the `run_config` argument for <PyObject section="jobs" module="dagster" object="JobDefinition.execute_in_process" /> or <PyObject section="execution" module="dagster" object="materialize"/>. This takes a <PyObject section="config" module="dagster" object="RunConfig"/> object, within which we can supply config on a per-op or per-asset basis. The config is specified as a dictionary, with the keys corresponding to the op/asset names and the values corresponding to the config values.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_execute_with_config" endBefore="end_execute_with_config" />

</TabItem>
<TabItem value="Dagster UI">

From the UI's **Launchpad** tab, you can supply config as YAML using the config editor. Here, the YAML schema matches the layout of the defined config class. The editor has typeahead, schema validation, and schema documentation.

You can also click the **Scaffold Missing Config** button to generate dummy values based on the config schema. Note that a modal containing the Launchpad editor will pop up if you attempt to materialize an asset with a defined `config`.

![Config in the Dagster UI](/images/guides/operate/config-ui.png)

</TabItem>
<TabItem value="Command line">

### Command line

When executing a job from Dagster's CLI with [`dagster job execute`](/api/python-api/cli#dagster-job), you can put config in a YAML file:

```YAML file=/concepts/configuration/good.yaml
ops:
  op_using_config:
    config:
      person_name: Alice
```

And then pass the file path with the `--config` option:

```bash
dagster job execute --config my_config.yaml
```

</TabItem>
</Tabs>

## Validation

Dagster validates any provided run config against the corresponding Pydantic model. It will abort execution with a <PyObject section="errors" module="dagster" object="DagsterInvalidConfigError"/> or Pydantic `ValidationError` if validation fails. For example, both of the following will fail, because there is no `nonexistent_config_value` in the config schema:

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_execute_with_bad_config" endBefore="end_execute_with_bad_config" />

### Using environment variables with config

Assets and ops can be configured using environment variables by passing an <PyObject section="resources" module="dagster" object="EnvVar" /> when constructing a config object. This is useful when the value is sensitive or may vary based on environment. If using Dagster+, environment variables can be [set up directly in the UI](/guides/deploy/using-environment-variables-and-secrets).

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/guides/dagster/pythonic_config/pythonic_config.py" startAfter="start_execute_with_config_envvar" endBefore="end_execute_with_config_envvar" />

Refer to the [Environment variables and secrets guide](/guides/deploy/using-environment-variables-and-secrets) for more general info about environment variables in Dagster.

## Next steps

Config is a powerful tool for making Dagster pipelines more flexible and observable. For a deeper dive into the supported config types, see [the advanced config types documentation](advanced-config-types). For more information on using resources, which are a powerful way to encapsulate reusable logic, see [the Resources guide](/guides/build/external-resources).
