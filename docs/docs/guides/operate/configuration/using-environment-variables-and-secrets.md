---
description: Dagster environment variables allow you to define various configuration options for your Dagster application and securely set up secrets.
sidebar_position: 300
title: Using environment variables and secrets in Dagster code
---

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

:::info

For more information on using environment variables with [Dagster components](/guides/build/components), see [Using environment variables with components](/guides/build/components/using-environment-variables-in-components).

:::

## Declaring environment variables

How environment variables are declared depends on whether you're developing locally or have already deployed your Dagster project.

<Tabs>
<TabItem value="Local development">

As of Dagster 1.1.0, using `.env` files is supported for loading environment variables into local environments. A `.env` file is a text file containing key-value pairs that is used locally, but not checked into source control. Using a `.env` file allows you to develop and test locally without putting sensitive info at risk. For example:

```shell
# .env

DATABASE_NAME=staging
DATABASE_SCHEMA=sales
DATABASE_USERNAME=salesteam
DATABASE_PASSWORD=supersecretstagingpassword
```

If Dagster detects a `.env` file in the same folder where the [webserver](/guides/operate/webserver) is launched, it will automatically load the environment variables in the file. This also applies to variables [exported from Dagster+](/deployment/dagster-plus/management/environment-variables/dagster-ui#export)

When using a `.env` file, keep the following in mind:

- The `.env` file must be in the same folder where the webserver is launched
- Any time the `.env` file is modified, the workspace must be re-loaded to make the Dagster webserver aware of the changes

</TabItem>
<TabItem value="Dagster+">

Environment variables can be set a variety of ways in Dagster+:

- Directly in the UI
- Via agent configuration (Hybrid deployments only)

If using the UI, you can also [export locally-scoped variables to a `.env` file](/deployment/dagster-plus/management/environment-variables/dagster-ui#export), which you can then use to develop locally.

Refer to the [Dagster+ environment variables guide](/deployment/dagster-plus/management/environment-variables) for more info.

</TabItem>
<TabItem value="Dagster open source">

How environment variables are set for Dagster projects deployed on your infrastructure depends on **where** Dagster is deployed. Refer to the deployment guide for your platform for more info:

- [Amazon Web Services EC2 / ECS](/deployment/oss/deployment-options/aws)
- [GCP](/deployment/oss/deployment-options/gcp)
- [Docker](/deployment/oss/deployment-options/docker)
- [Kubernetes](/deployment/oss/deployment-options/kubernetes/deploying-to-kubernetes)

</TabItem>
</Tabs>

## Accessing environment variables

In this section, we'll demonstrate how to access environment variables once they've been declared. There are two ways to do this:

- [In Python code](#in-python-code)
- [From Dagster configuration](#from-dagster-configuration), which incorporates environment variables into the Dagster config system

### In Python code

To access environment variables in your code, you can either use the [`os.getenv`](https://docs.python.org/3/library/os.html#os.getenv) function or the Dagster <PyObject section="resources" module="dagster" object="EnvVar"/> class.

- **When you use `os.getenv`**, the variable's value is retrieved when Dagster loads the code location and **will** be visible in the UI.
- **When you use EnvVar**, the variable's value is retrieved at runtime and **won't** be visible in the UI.

Using the `EnvVar` approach has a few unique benefits:

- **Improved observability.** The UI will display information about configuration values sourced from environment variables.
- **Secret values are hidden in the UI.** Secret values are hidden in the Launchpad, Resources page, and other places where configuration is displayed.
- **Simplified testing.** Because you can provide string values directly to configuration rather than environment variables, testing may be easier.

#### os.getenv function

Below is an example of retrieving an environment variable with `os.getenv`:

```python
import os

database_name = os.getenv("DATABASE_NAME")
```

You can also use `os.getenv` to access [built-in environment variables for Dagster+](/deployment/dagster-plus/management/environment-variables/built-in):

```python
import os

deployment_name = os.getenv("DAGSTER_CLOUD_DEPLOYMENT_NAME")
```

For a real-world example, see the [Dagster+ branch deployments example](#dagster-branch-deployments).

#### Dagster EnvVar class

To use the `EnvVar` approach, call the `get_value()` method on the Dagster <PyObject section="resources" module="dagster" object="EnvVar"/> class:

```python
import dagster as dg

database_name = dg.EnvVar('DATABASE_NAME').get_value()
```

### From Dagster configuration

[Configurable Dagster objects](/guides/operate/configuration/run-configuration) (such as ops, assets, resources, I/O managers, and so on) can accept configuration from environment variables with `EnvVar`. These environment variables are retrieved at launch time, rather than on initialization as with `os.getenv`.

<Tabs>
<TabItem value="In Python code">

To access an environment variable as part of a Dagster configuration in Python code, you may use the following special syntax:

```python
"PARAMETER_NAME": dg.EnvVar("ENVIRONMENT_VARIABLE_NAME")
```

For example:

```python
"access_token": dg.EnvVar("GITHUB_ACCESS_TOKEN")
```

And when specifying an integer number:

```python
"database_port": dg.EnvVar.int("DATABASE_PORT")
```

</TabItem>
<TabItem value="In YAML or config dictionaries">

To access an environment variable as part of a Dagster configuration in YAML or in a config dictionary, use the following syntax:

```python
"PARAMETER_NAME": {"env": "ENVIRONMENT_VARIABLE_NAME"}
```

For example:

```python
"access_token": {"env": "GITHUB_ACCESS_TOKEN"}
```

For more information, see the [Handling secrets](#handling-secrets) and [Per-environment configuration](#per-environment-configuration) sections.

</TabItem>
</Tabs>

## Handling secrets

:::note

The example code in this section follows the structure of a Dagster project created with the [`create-dagster CLI](/api/clis/create-dagster). To create a Dagster project with this structure, see [Creating a new Dagster project](/guides/build/projects/creating-a-new-project).

:::

Using environment variables to provide secrets ensures sensitive information won't be visible in your code or the launchpad in the UI. In Dagster, we recommend using [configuration](/guides/operate/configuration/run-configuration) and [resources](/guides/build/external-resources) to manage secrets.

A resource is typically used to connect to an external service or system, such as a database. Resources can be configured separately from your assets, allowing you to define them once and reuse them as needed.

Let's take a look at an example that creates a resource called `SomeResource` and supplies it to assets. Let's start by looking at the resource:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/configuration/env_vars_and_secrets/resources.py"
  title="src/<project_name>/defs/resources.py"
/>

Let's review what's happening here:

- This code creates a resource named `SomeResource`
- By subclassing <PyObject section="resources" module="dagster" object="ConfigurableResource" /> and specifying the `access_token` field, we're telling Dagster that we want to be able to configure the resource with an `access_token` parameter, which is a string value

By including a reference to `SomeResource` in a `@dg.definitions`-decorated function, we make that resource available to assets defined elsewhere in the `src/<project_name>/defs` directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/configuration/env_vars_and_secrets/assets.py"
  title="src/<project_name>/defs/assets.py"
  startAfter="start"
  endBefore="end"
/>

As storing secrets in configuration is bad practice, we'll use an environment variable:

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/configuration/env_vars_and_secrets/resources_v2.py"
  title="src/<project_name>/defs/resources.py"
/>

In this code, we pass configuration information to the resource when we construct it. In this example, we're telling Dagster to load the `access_token` from the `MY_ACCESS_TOKEN` environment variable by wrapping it in `dg.EnvVar`.

## Parameterizing pipeline behavior

Using environment variables, you define how your code should execute at runtime.

### Per-environment configuration

In this example, we'll demonstrate how to use different I/O manager configurations for `local` and `production` environments using [configuration](/guides/operate/configuration/run-configuration) (specifically the configured API) and [resources](/guides/build/external-resources).

This example is adapted from the [Transitioning data pipelines from development to production guide](/guides/operate/dev-to-prod):

<CodeExample
  path="docs_snippets/docs_snippets/guides/operate/configuration/env_vars_and_secrets/per_env_config.py"
  title="src/<project_name>/defs/resources.py"
/>

Let's review what's happening here:

- We've created a dictionary of resource definitions called `resources`, with sections for `local` and `production` environments. In this example, we're using a [Pandas Snowflake I/O manager](/integrations/libraries/snowflake/dagster-snowflake-pandas).
- For both `local` and `production`, we constructed the I/O manager using environment-specific run configuration.
- Following the `resources` dictionary, we define the `deployment_name` variable, which determines the current executing environment. This variable defaults to `local`, ensuring that `DAGSTER_DEPLOYMENT=PRODUCTION` must be set to use the `production` configuration.

### Dagster+ branch deployments

:::note

This section is only applicable to Dagster+.

:::

You can determine the current deployment type ([branch deployment](/deployment/dagster-plus/deploying-code/branch-deployments) or [full deployment](/deployment/dagster-plus/deploying-code/full-deployments)) at runtime with the `DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT` environment variable. Using this information, you can write code that executes differently when in a branch deployment or a full deployment.

```python

def get_current_env():
  is_branch_depl = os.getenv("DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT") == "1"
  assert is_branch_depl != None  # env var must be set
  return "branch" if is_branch_depl else "prod"

```

This function checks the value of `DAGSTER_CLOUD_IS_BRANCH_DEPLOYMENT` and, if equal to `1`, returns a variable with the value of `branch`. This indicates that the current deployment is a branch deployment. Otherwise, the deployment is a full deployment and `is_branch_depl` will be returned with a value of `prod`.

## Troubleshooting

| Error                                                                                                                                                              | Description                                                                                                                                                                                                               | Solution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **You have attempted to fetch the environment variable "[variable]" which is not set. In order for this execution to succeed it must be set in this environment.** | Surfacing when a run is launched in the UI, this error means that an environment variable set using <PyObject section="config" module="dagster" object="StringSource" /> could not be found in the executing environment. | Verify that the environment variable is named correctly and accessible in the environment.<ul><li>**If developing locally and using a `.env` file**, try reloading the workspace in the UI. The workspace must be reloaded any time this file is modified for the UI to be aware of the changes.</li><li>**If using Dagster+**:</li><ul><li>Verify that the environment variable is [scoped to the environment and code location](/deployment/dagster-plus/management/environment-variables/dagster-ui#scope) if using the built-in secrets manager</li><li>Verify that the environment variable was correctly configured and added to your [agent's configuration](/deployment/dagster-plus/management/environment-variables/agent-config)</li></ul></ul> |
| **No environment variables in `.env` file.**                                                                                                                       | Dagster located and attempted to load a local `.env` file while launching `dagster-webserver`, but couldn't find any environment variables in the file.                                                                   | If this is unexpected, verify that your `.env` is correctly formatted and located in the same folder where you're running `dagster-webserver`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
