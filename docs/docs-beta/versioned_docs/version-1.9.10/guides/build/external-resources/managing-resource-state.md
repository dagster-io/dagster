---
title: Managing resource state
sidebar_position: 900
---

Once a resource reaches a certain complexity, you may want to manage the state of the resource over its lifetime. This is useful for resources that require special initialization or cleanup. `ConfigurableResource` is a data class meant to encapsulate config, but also provides lifecycle hooks to manage the state of the resource.

You can mark any private state attributes using Pydantic's [`PrivateAttr`](https://docs.pydantic.dev/latest/usage/models/#private-model-attributes). These attributes, which must start with an underscore, won't be included in the resource's config.

## Lifecycle hooks

When a resource is initialized during a Dagster run, the `setup_for_execution` method is called. This method is passed an <PyObject section="resources" module="dagster" object="InitResourceContext" /> object, which contains the resource's config and other run information. The resource can use this context to initialize any state it needs for the duration of the run.

Once a resource is no longer needed, the `teardown_after_execution` method is called. This method is passed the same context object as `setup_for_execution`. This method can be useful for cleaning up any state that was initialized in `setup_for_execution`.

`setup_for_execution` and `teardown_after_execution` are each called once per run, per process. When using the in-process executor, this means that they will be called once per run. When using the multiprocess executor, each process's instance of the resource will be initialized and torn down.

In the following example, we set up an API token for a client resource based on the username and password provided in the config. The API token can then be used to query an API in the asset body.

```python file=/concepts/resources/pythonic_resources.py startafter=start_with_state_example endbefore=end_with_state_example dedent=4
from dagster import ConfigurableResource, InitResourceContext, asset
import requests

from pydantic import PrivateAttr

class MyClientResource(ConfigurableResource):
    username: str
    password: str

    _api_token: str = PrivateAttr()

    def setup_for_execution(self, context: InitResourceContext) -> None:
        # Fetch and set up an API token based on the username and password
        self._api_token = requests.get(
            "https://my-api.com/token", auth=(self.username, self.password)
        ).text

    def get_all_users(self):
        return requests.get(
            "https://my-api.com/users",
            headers={"Authorization": self._api_token},
        )

@asset
def my_asset(client: MyClientResource):
    return client.get_all_users()
```

For more complex use cases, you can override the `yield_for_execution`. By default, this context manager calls `setup_for_execution`, yields the resource, and then calls `teardown_after_execution`, but you can override it to provide any custom behavior. This is useful for resources that require a context to be open for the duration of a run, such as database connections or file handles.

```python file=/concepts/resources/pythonic_resources.py startafter=start_with_complex_state_example endbefore=end_with_complex_state_example dedent=4
from dagster import ConfigurableResource, asset, InitResourceContext
from contextlib import contextmanager
from pydantic import PrivateAttr

class DBConnection:
    ...

    def query(self, body: str): ...

@contextmanager
def get_database_connection(username: str, password: str): ...

class MyClientResource(ConfigurableResource):
    username: str
    password: str

    _db_connection: DBConnection = PrivateAttr()

    @contextmanager
    def yield_for_execution(self, context: InitResourceContext):
        # keep connection open for the duration of the execution
        with get_database_connection(self.username, self.password) as conn:
            # set up the connection attribute so it can be used in the execution
            self._db_connection = conn

            # yield, allowing execution to occur
            yield self

    def query(self, body: str):
        return self._db_connection.query(body)

@asset
def my_asset(client: MyClientResource):
    client.query("SELECT * FROM my_table")
```
