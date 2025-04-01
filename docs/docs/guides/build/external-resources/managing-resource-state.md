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

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_with_state_example" endBefore="end_with_state_example" />

For more complex use cases, you can override the `yield_for_execution`. By default, this context manager calls `setup_for_execution`, yields the resource, and then calls `teardown_after_execution`, but you can override it to provide any custom behavior. This is useful for resources that require a context to be open for the duration of a run, such as database connections or file handles.

{/* TODO add dedent=4 prop when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_with_complex_state_example" endBefore="end_with_complex_state_example" />
