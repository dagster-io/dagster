---
title: Configuring resources
sidebar_position: 200
---

You can configure resources with environment variables or at launch time. Additionally, you can define resources that depend on other resources to manage common configuration.

## Using environment variables with resources

Resources can be configured using environment variables, which is useful for secrets or other environment-specific configuration. If you're using [Dagster+](/dagster-plus/), environment variables can be [configured directly in the UI](/dagster-plus/deployment/management/environment-variables).

To use environment variables, pass an <PyObject section="resources" module="dagster" object="EnvVar" /> when constructing the resource. `EnvVar` inherits from `str` and can be used to populate any string config field on a resource. The value of the environment variable will be evaluated when a run is launched.

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resources_env_vars endbefore=end_new_resources_env_vars dedent=4
from dagster import EnvVar, Definitions, ConfigurableResource

class CredentialsResource(ConfigurableResource):
    username: str
    password: str

defs = Definitions(
    assets=...,
    resources={
        "credentials": CredentialsResource(
            username=EnvVar("MY_USERNAME"),
            password=EnvVar("MY_PASSWORD"),
        )
    },
)
```

**What about `os.getenv()`?** When `os.getenv()` is used, the value of the variable is retrieved when Dagster loads the code location. Using `EnvVar` not only tells Dagster to retrieve the value at runtime, but also not to display the value in the UI.

<!-- Lives in /next/components/includes/EnvVarsBenefits.mdx -->

For more information on using environment variables with Dagster, refer to the [Environment variables guide](/todo).

## Configuring resources at launch time

In some cases, you may want to specify configuration for a resource at launch time, in the Launchpad or in a <PyObject section="schedules-sensors" module="dagster" object="RunRequest" /> for a [schedule](/guides/automate/schedules/) or [sensor](/guides/automate/sensors/). For example, you may want a sensor-triggered run to specify a different target table in a database resource for each run.

You can use the `configure_at_launch()` method to defer the construction of a configurable resource until launch time:

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_runtime endbefore=end_new_resource_runtime dedent=4
from dagster import ConfigurableResource, Definitions, asset

class DatabaseResource(ConfigurableResource):
    table: str

    def read(self): ...

@asset
def data_from_database(db_conn: DatabaseResource):
    return db_conn.read()

defs = Definitions(
    assets=[data_from_database],
    resources={"db_conn": DatabaseResource.configure_at_launch()},
)
```

### Providing resource launch time configuration in Python code

Then, configuration for the resource can be provided at launch time in the Launchpad or in Python code using the `config` parameter of the <PyObject section="schedules-sensors" module="dagster" object="RunRequest" />:

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_runtime_launch endbefore=end_new_resource_runtime_launch dedent=4
from dagster import sensor, define_asset_job, RunRequest, RunConfig

update_data_job = define_asset_job(
    name="update_data_job", selection=[data_from_database]
)

@sensor(job=update_data_job)
def table_update_sensor():
    tables = ...
    for table_name in tables:
        yield RunRequest(
            run_config=RunConfig(
                resources={
                    "db_conn": DatabaseResource(table=table_name),
                },
            ),
        )
```

## Resources that depend on other resources

In some situations, you may want to define a resource that depends on other resources. This is useful for common configuration. For example, separate resources for a database and for a filestore may both depend on credentials for a particular cloud provider. Defining these credentials as a separate, nested resource allows you to specify configuration in a single place. It also makes it easier to test resources, since the nested resource can be mocked.

In this case, you can list that nested resource as an attribute of the resource class:

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resources_nesting endbefore=end_new_resources_nesting dedent=4
from dagster import Definitions, ConfigurableResource, ResourceDependency

class CredentialsResource(ConfigurableResource):
    username: str
    password: str

class FileStoreBucket(ConfigurableResource):
    credentials: ResourceDependency[CredentialsResource]
    region: str

    def write(self, data: str):
        # We can access the credentials resource via `self.credentials`,
        # which will be an initialized instance of `CredentialsResource`
        get_filestore_client(
            username=self.credentials.username,
            password=self.credentials.password,
            region=self.region,
        ).write(data)

defs = Definitions(
    assets=[my_asset],
    resources={
        "bucket": FileStoreBucket(
            credentials=CredentialsResource(
                username="my_user", password="my_password"
            ),
            region="us-east-1",
        ),
    },
)
```

If you prefer to provide the configuration for credentials at launch time, use the `configure_at_launch()` method to defer the construction of the `CredentialsResource` until launch time.

Because `credentials` requires launch time configuration through the launchpad, it must also be passed to the <PyObject section="definitions" module="dagster" object="Definitions" /> object, so that configuration can be provided at launch time. Nested resources only need to be passed to the <PyObject section="definitions" module="dagster" object="Definitions" /> object if they require launch time configuration.

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_dep_job_runtime endbefore=end_new_resource_dep_job_runtime dedent=4
credentials = CredentialsResource.configure_at_launch()

defs = Definitions(
    assets=[my_asset],
    resources={
        "credentials": credentials,
        "bucket": FileStoreBucket(
            credentials=credentials,
            region="us-east-1",
        ),
    },
)
```

## Next steps

Resources are a powerful way to encapsulate reusable logic in your assets and ops. For more information on the supported config types for resources, see [the advanced config types documentation](/todo). For information on the Dagster config system, which you can use to parameterize assets and ops, refer to the [run configuration documentation](/todo).