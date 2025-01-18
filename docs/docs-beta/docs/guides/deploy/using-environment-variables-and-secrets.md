---
title: Using environment variables and secrets
sidebar_position: 400
---

# Using environment variables and secrets

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

## Declaring environment variables

How environment variables are declared depends on whether you're developing locally or have already deployed your Dagster project.

<Tabs>
<TabItem value="Local development">

**Local development**

As of Dagster 1.1.0, using `.env` files is supported for loading environment variables into local environments. A `.env` file is a text file containing key-value pairs that is used locally, but not checked into source control. Using a `.env` file allows you to develop and test locally without putting sensitive info at risk. For example:

```shell
# .env

DATABASE_NAME=staging
DATABASE_SCHEMA=sales
DATABASE_USERNAME=salesteam
DATABASE_PASSWORD=supersecretstagingpassword
```

If Dagster detects a `.env` file in the same folder where `dagster-webserver` or `dagster-daemon` is launched, it will automatically load the environment variables in the file. This also applies to variables [exported from Dagster+](/dagster-plus/deployment/management/environment-variables/dagster-ui#export)


When using a `.env` file, keep the following in mind:

- The `.env` file must be in the same folder where `dagster-webserver` or `dagster-daemon` is launched
- Any time the `.env` file is modified, the workspace must be re-loaded to make the Dagster webserver/UI aware of the changes

</TabItem>
<TabItem value="Dagster open source">

**Dagster open source**

How environment variables are set for Dagster projects deployed on your infrastructure depends on **where** Dagster is deployed. Refer to the deployment guide for your platform for more info:

* [Amazon Web Services EC2 / ECS](/guides/deploy/deployment-options/aws)
* [GCP](/guides/deploy/deployment-options/gcp)
* [Docker](/guides/deploy/deployment-options/docker)
* [Kubernetes](/guides/deploy/deployment-options/kubernetes/deploying-to-kubernetes)

</TabItem>
</Tabs>

## Accessing environment variables

In this section, we'll demonstrate how to access environment variables once they've been declared. There are two ways to do this:

- [In Python code](#in-python-code), which isn't specific to Dagster
- [From Dagster configuration](#from-dagster-configuration), which incorporates environment variables into the Dagster config system

### In Python code

To access environment variables in your Dagster code, you can use [`os.getenv`](https://docs.python.org/3/library/os.html#os.getenv):

```python
import os

database_name = os.getenv("DATABASE_NAME")
```

You can also call the `get_value()` method on the `EnvVar`:

```python
from dagster import EnvVar

database_name = EnvVar('DATABASE_NAME').get_value()
```

### From Dagster configuration

[Configurable Dagster objects](/todo) - such as ops, assets, resources, I/O managers, and so on - can accept configuration from environment variables. Dagster provides a native way to specify environment variables in your configuration. These environment variables are retrieved at launch time, rather than on initialization as with `os.getenv`. Refer to the [next section](#using-envvar-vs-osgetenv) for more info.

<Tabs>
<TabItem value="In Python code">

**In Python code**

To access an environment variable as part of a Dagster configuration in Python code, you may use the following special syntax:

```python
"PARAMETER_NAME": EnvVar("ENVIRONMENT_VARIABLE_NAME")
```

For example:

```python
"access_token": EnvVar("GITHUB_ACCESS_TOKEN")
```

And when specifying an integer number:

```python
"database_port": EnvVar.int("DATABASE_PORT")
```

</TabItem>
<TabItem value="In YAML or config dictionaries">

**In YAML or config dictionaries**

To access an environment variable as part of a Dagster configuration in YAML or in a config dictionary, use the following syntax:

```python
"PARAMETER_NAME": {"env": "ENVIRONMENT_VARIABLE_NAME"}
```

For example:

```python
"access_token": {"env": "GITHUB_ACCESS_TOKEN"}
```

Refer to the [Handling secrets section](#handling-secrets) and [Per-environment configuration example](#per-environment-configuration-example) for examples.

</TabItem>
</Tabs>

### Using EnvVar vs os.getenv

We just covered two different ways to access environment variables in Dagster. So, which one should you use? When choosing an approach, keep the following in mind:

- **When `os.getenv` is used**, the variable's value is retrieved when Dagster loads the [code location](/guides/deploy/code-locations/) and **will** be visible in the UI.
- **When `EnvVar` is used**, the variable's value is retrieved at runtime and **won't** be visible in the UI.

Using the `EnvVar` approach has a few unique benefits:

- **Improved observability.** The UI will display information about configuration values sourced from environment variables.
- **Secret values are hidden in the UI.** Secret values are hidden in the Launchpad, Resources page, and other places where configuration is displayed.
- **Simplified testing.** Because you can provide string values directly to configuration rather than environment variables, testing may be easier.

## Handling secrets

Using environment variables to provide secrets ensures sensitive info won't be visible in your code or the launchpad in the UI. In Dagster, best practice for handling secrets uses [configuration](/todo) and [resources](/guides/build/external-resources/).

A resource is typically used to connect to an external service or system, such as a database. Resources can be configured separately from the rest of your app, allowing you to define it once and reuse it as needed.

Let's take a look at an example from the [Dagster Crash Course](https://dagster.io/blog/dagster-crash-course-oct-2022), which creates a GitHub resource and supplies it to assets. Let's start by looking at the resource:

```python
## resources.py

from dagster import StringSource, resource
from github import Github

class GithubClientResource(ConfigurableResource):
  access_token: str

  def get_client(self) -> Github:
    return Github(self.access_token)
```

Let's review what's happening here:

- This code creates a GitHub resource named `GithubClientResource`
- By subclassing <PyObject section="resources" module="dagster" object="ConfigurableResource" /> and specifying the `access_token` field, we're telling Dagster that we want to be able to configure the resource with an `access_token` parameter
- Since `access_token` is a string value, this config parameter can either be:
  - An environment variable, or
  - Provided directly in the configuration

As storing secrets in configuration is bad practice, we'll opt for using an environment variable. In this code, we're configuring the resource supplying it to our assets:

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/using_environment_variables_and_secrets/repository.py startafter=start endbefore=end
# definitions.py

from my_dagster_project import assets
from my_dagster_project.resources import GithubClientResource

from dagster import Definitions, EnvVar, load_assets_from_package_module

defs = Definitions(
    assets=load_assets_from_package_module(assets),
    resources={
        "github_api": GithubClientResource(access_token=EnvVar("GITHUB_ACCESS_TOKEN"))
    },
)
```

Let's review what's happening here:

- We pass configuration info to the resource when we construct it. In this example, we're telling Dagster to load the `access_token` from the `GITHUB_ACCESS_TOKEN` environment variable by wrapping it in `EnvVar`.
- We're adding that resource to our <PyObject section="definitions" module="dagster" object="Definitions" /> object so it's available for our assets.

## Parameterizing pipeline behavior

Using environment variables, you define how your code should execute at runtime.

- [Per-environment configuration example](#per-environment-configuration-example)

### Per-environment configuration example

In this example, we'll demonstrate how to use different I/O manager configurations for `local` and `production` environments using [configuration](/todo) (specifically the configured API) and [resources](/guides/build/external-resources/).

This example is adapted from the [Transitioning data pipelines from development to production guide](/guides/deploy/dev-to-prod):

{/* TODO convert to <CodeExample> */}
```python file=/guides/dagster/using_environment_variables_and_secrets/repository_v2.py startafter=start_new endbefore=end_new
# definitions.py

resources = {
    "local": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("DEV_SNOWFLAKE_USER"),
            password=EnvVar("DEV_SNOWFLAKE_PASSWORD"),
            database="LOCAL",
            schema=EnvVar("DEV_SNOWFLAKE_SCHEMA"),
        ),
    },
    "production": {
        "snowflake_io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user="system@company.com",
            password=EnvVar("SYSTEM_SNOWFLAKE_PASSWORD"),
            database="PRODUCTION",
            schema="HACKER_NEWS",
        ),
    },
}

deployment_name = os.getenv("DAGSTER_DEPLOYMENT", "local")

defs = Definitions(
    assets=[items, comments, stories], resources=resources[deployment_name]
)
```

Let's review what's happening here:

- We've created a dictionary of resource definitions, `resources`, named after our `local` and `production` environments. In this example, we're using a [Pandas Snowflake I/O manager](/api/python-api/libraries/dagster-snowflake-pandas).
- For both `local` and `production`, we constructed the I/O manager using environment-specific run configuration. Note the differences in configuration between `local` and `production`, specifically where environment variables were used.
- Following the `resources` dictionary, we define the `deployment_name` variable, which determines the current executing environment. This variable defaults to `local`, ensuring that `DAGSTER_DEPLOYMENT=PRODUCTION` must be set to use the `production` configuration.

## Troubleshooting

| Error | Description | Solution     |
|-------|-------------|--------------|
| **You have attempted to fetch the environment variable "[variable]" which is not set. In order for this execution to succeed it must be set in this environment.** | Surfacing when a run is launched in the UI, this error means that an environment variable set using <PyObject section="config" module="dagster" object="StringSource" /> could not be found in the executing environment. | Verify that the environment variable is named correctly and accessible in the environment.<ul><li>**If developing locally and using a `.env` file**, try reloading the workspace in the UI. The workspace must be reloaded any time this file is modified for the UI to be aware of the changes.</li><li>**If using Dagster+**:</li><ul><li>Verify that the environment variable is [scoped to the environment and code location](/dagster-plus/deployment/management/environment-variables/dagster-ui#scope) if using the built-in secrets manager</li><li>Verify that the environment variable was correctly configured and added to your [agent's configuration](/dagster-plus/deployment/management/environment-variables/agent-config)</li></ul></ul> |
| **No environment variables in `.env` file.** | Dagster located and attempted to load a local `.env` file while launching `dagster-webserver`, but couldn't find any environment variables in the file. | If this is unexpected, verify that your `.env` is correctly formatted and located in the same folder where you're running `dagster-webserver`. |
