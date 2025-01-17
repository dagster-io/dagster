---
title: Defining resources
sidebar_position: 100
---

Typically, resources are defined by subclassing <PyObject section="resources" module="dagster" object="ConfigurableResource"/>. Resources typically have a set of [configuration values](/todo), which are used to specify information like account identifiers, API keys, or database names when interfacing with an external tool or service. This configuration schema is specified by attributes on the class.

The configuration system has a few advantages over plain Python parameter passing. Configured values can be:

- Replaced at run launch time in the Launchpad in Dagster UI, the GraphQL API, or the Python API
- Displayed in the Dagster UI
- Set dynamically using environment variables, resolved at runtime

## With asset definitions

The following example demonstrates defining a subclass of <PyObject section="resources" module="dagster" object="ConfigurableResource"/> that represents a connection to an external service. The resource can be configured by constructing it in the <PyObject section="definitions" module="dagster" object="Definitions" /> call.

You can define methods on the resource class which depend on config values.

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resources_configurable_defs endbefore=end_new_resources_configurable_defs dedent=4
from dagster import asset, Definitions, ConfigurableResource
import requests
from requests import Response

class MyConnectionResource(ConfigurableResource):
    username: str

    def request(self, endpoint: str) -> Response:
        return requests.get(
            f"https://my-api.com/{endpoint}",
            headers={"user-agent": "dagster"},
        )

@asset
def data_from_service(my_conn: MyConnectionResource) -> Dict[str, Any]:
    return my_conn.request("/fetch_data").json()

defs = Definitions(
    assets=[data_from_service],
    resources={
        "my_conn": MyConnectionResource(username="my_user"),
    },
)
```

Assets specify resource dependencies by annotating the resource as a parameter to the asset function.

To provide resource values to assets, attach them to the <PyObject section="definitions" module="dagster" object="Definitions" /> objects. These resources are automatically passed to the function at runtime.

## With sensors

[Sensors](/guides/automate/sensors/) use resources in the same way as assets, which can be useful for querying external services for data.

To specify resource dependencies on a sensor, annotate the resource type as a parameter to the sensor's function. For more information and examples, see the [Sensors documentation](/guides/automate/sensors/using-resources-in-sensors).

## With schedules

[Schedules](/guides/automate/schedules) can use resources in case your schedule logic needs to interface with an external tool or to make your schedule logic more testable.

To specify resource dependencies on a schedule, annotate the resource type as a parameter to the schedule's function. For more information, see "[Using resources in schedules](/guides/automate/schedules/using-resources-in-schedules).

## With jobs

The following example defines a subclass of <PyObject section="resources" module="dagster" object="ConfigurableResource"/> that represents a connection to an external service. The resource can be configured by constructing it in the <PyObject section="definitions" module="dagster" object="Definitions" /> call.

You can define methods on the resource class which depend on config values.

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resources_configurable_defs_ops endbefore=end_new_resources_configurable_defs_ops dedent=4
from dagster import Definitions, job, op, ConfigurableResource
import requests
from requests import Response

class MyConnectionResource(ConfigurableResource):
    username: str

    def request(self, endpoint: str) -> Response:
        return requests.get(
            f"https://my-api.com/{endpoint}",
            headers={"user-agent": "dagster"},
        )

@op
def update_service(my_conn: MyConnectionResource):
    my_conn.request("/update")

@job
def update_service_job():
    update_service()

defs = Definitions(
    jobs=[update_service_job],
    resources={
        "my_conn": MyConnectionResource(username="my_user"),
    },
)
```

There are many supported config types that can be used when defining resources. Refer to the [advanced config types documentation](/todo) for a more comprehensive overview of the available config types.