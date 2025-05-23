---
title: 'Managing code locations with Definitions'
description: "A code location is a collection of Dagster definitions loadable and accessible by Dagster's tools. Learn to create, load, and deploy code locations."
sidebar_position: 100
---

A code location is a collection of Dagster definitions loadable and accessible by Dagster's tools, such as the CLI, UI, and Dagster+. A code location comprises:

- A reference to a Python module that has an instance of <PyObject section="definitions" module="dagster" object="Definitions" /> in a top-level variable
- A Python environment that can successfully load that module

Definitions within a code location have a common namespace and must have unique names. This allows them to be grouped and organized by code location in tools.

![Code locations](/images/guides/deploy/code-locations/code-locations-diagram.png)

A single deployment can have one or multiple code locations.

Code locations are loaded in a different process and communicate with Dagster system processes over an RPC mechanism. This architecture provides several advantages:

- When there is an update to user code, the Dagster webserver/UI can pick up the change without a restart.
- You can use multiple code locations to organize jobs, but still work on all of your code locations using a single instance of the webserver/UI.
- The Dagster webserver process can run in a separate Python environment from user code so job dependencies don't need to be installed into the webserver environment.
- Each code location can be sourced from a separate Python environment, so teams can manage their dependencies (or even their Python versions) separately.

## Relevant APIs

| Name                                                                     | Description                                                                                                                                       |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="definitions" module="dagster" object="Definitions" /> | The object that contains all the definitions defined within a code location. Definitions include assets, jobs, resources, schedules, and sensors. |

## Defining code locations

To define a code location, create a top-level variable that contains a <PyObject section="definitions" module="dagster" object="Definitions" /> object in a Python module. For example:

```python
# definitions.py

defs = Definitions(
    assets=[dbt_customers_asset, dbt_orders_asset],
    schedules=[bi_weekly_schedule],
    sensors=[new_data_sensor],
    resources=[dbt_resource],
)
```

It is recommended to include definitions in a Python module named `definitions.py`.

## Deploying and loading code locations

- [Local development](#local-development)
- [Dagster+ deployment](#dagster-deployment)
- [Open source deployment](#open-source-deployment)

### Local development

<Tabs>
<TabItem value="From a file" label="From a file">

Dagster can load a file directly as a code location. In the following example, we used the `-f` argument to supply the name of the file:

```shell
dagster dev -f my_file.py
```

This command loads the definitions in `my_file.py` as a code location in the current Python environment.

You can also include multiple files at a time, where each file will be loaded as a code location:

```shell
dagster dev -f my_file.py -f my_second_file.py
```

</TabItem>
<TabItem value="From a module" label="From a module">

Dagster can also load Python modules as [code locations](/guides/deploy/code-locations/). When this approach is used, Dagster loads the definitions defined in the module passed to the command line.

We recommend defining a variable containing the <PyObject section="definitions" module="dagster" object="Definitions" /> object in a submodule named `definitions` inside the Python module. In practice, the submodule can be created by adding a file named `definitions.py` at the root level of the Python module.

As this style of development eliminates an entire class of Python import errors, we strongly recommend it for Dagster projects deployed to production.

In the following example, we used the `-m` argument to supply the name of the module and where to find the definitions:

```shell
dagster dev -m your_module_name.definitions
```

This command loads the definitions in the variable containing the <PyObject section="definitions" module="dagster" object="Definitions" /> object in the `definitions` submodule in the current Python environment.

You can also include multiple modules at a time, where each module will be loaded as a code location:

```shell
dagster dev -m your_module_name.definitions -m your_second_module.definitions
```

</TabItem>
<TabItem value="Without command line arguments" label="Without command line arguments">

To load definitions without supplying command line arguments, you can use the `pyproject.toml` file. This file, included in all Dagster example projects, contains a `tool.dagster` section with a `module_name` variable:

```toml
[tool.dagster]
module_name = "your_module_name.definitions"  ## name of project's Python module and where to find the definitions
code_location_name = "your_code_location_name"  ## optional, name of code location to display in the Dagster UI
```

When defined, you can run this in the same directory as the `pyproject.toml` file:

```shell
dagster dev
```

Instead of this:

```shell
dagster dev -m your_module_name.definitions
```

You can also include multiple modules at a time using the `pyproject.toml` file, where each module will be loaded as a code location:

```toml
[tool.dagster]
modules = [{ type = "module", name = "foo" }, { type = "module", name = "bar" }]
```

</TabItem>
</Tabs>

Fore more information about local development, including how to configure your local instance, see "[Running Dagster locally](/guides/deploy/deployment-options/running-dagster-locally)".

### Dagster+ deployment

See the [Dagster+ code locations documentation](/dagster-plus/deployment/code-locations/).

### Open source deployment

The `workspace.yaml` file is used to load code locations for open source (OSS) deployments. This file specifies how to load a collection of code locations and is typically used in advanced use cases. For more information, see "[workspace.yaml reference](/guides/deploy/code-locations/workspace-yaml)".

## Troubleshooting

| Error                                                                | Description and resolution                                                                                                                                                                                                                                    |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cannot have more than one Definitions object defined at module scope | Dagster found multiple <PyObject section="definitions" module="dagster" object="Definitions" /> objects in a single Python module. Only one <PyObject section="definitions" module="dagster" object="Definitions" /> object may be in a single code location. |
