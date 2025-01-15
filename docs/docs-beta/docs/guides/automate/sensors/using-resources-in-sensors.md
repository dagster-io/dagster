---
title: Using resources in sensors
sidebar_position: 100
unlisted: true
---

Dagster's [resources](/concepts/resources) system can be used with sensors to make it easier to call out to external systems and to make components of a sensor easier to plug in for testing purposes.

To specify resource dependencies, annotate the resource as a parameter to the sensor's function. Resources are provided by attaching them to your <PyObject object="Definitions" /> call.

Here, a resource is provided which provides access to an external API. The same resource could be used in the job or assets that the sensor triggers.

```python file=/concepts/resources/pythonic_resources.py startafter=start_new_resource_on_sensor endbefore=end_new_resource_on_sensor dedent=4
from dagster import (
    sensor,
    RunRequest,
    SensorEvaluationContext,
    ConfigurableResource,
    job,
    Definitions,
    RunConfig,
)
import requests
from typing import List

class UsersAPI(ConfigurableResource):
    url: str

    def fetch_users(self) -> list[str]:
        return requests.get(self.url).json()

@job
def process_user(): ...

@sensor(job=process_user)
def process_new_users_sensor(
    context: SensorEvaluationContext,
    users_api: UsersAPI,
):
    last_user = int(context.cursor) if context.cursor else 0
    users = users_api.fetch_users()

    num_users = len(users)
    for user_id in users[last_user:]:
        yield RunRequest(
            run_key=user_id,
            tags={"user_id": user_id},
        )

    context.update_cursor(str(num_users))

defs = Definitions(
    jobs=[process_user],
    sensors=[process_new_users_sensor],
    resources={"users_api": UsersAPI(url="https://my-api.com/users")},
)
```

For more information on resources, refer to the [Resources documentation](/concepts/resources). To see how to test schedules with resources, refer to the section on [Testing sensors with resources](#testing-sensors-with-resources).
