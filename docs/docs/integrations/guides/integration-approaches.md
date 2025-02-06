---
title: "Approaches to writing a Dagster integration"
sidebar_position: 100
unlisted: true
---

There are many approaches to writing an integration in Dagster. The choice of approach depends on the specific requirements of the integration, the level of control needed, and the complexity of the external system being integrated. The following are typical approaches that align with Dagster's best practices.

- [Resource providers](#resource-providers)
- [Factory methods](#factory-methods)
- [Multi-asset decorators](#multi-asset-decorators)
- [Pipes protocol](#pipes-protocol)

## Resource providers

One of the most fundamental features that can be implemented in an integration is a resource object to interface with an external service. For example, the `dagster-snowflake` integration provides a custom [SnowflakeResource](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-snowflake/dagster_snowflake/resources.py) that is a wrapper around the Snowflake `connector` object.

### Pros

- **Simple** Implementing a resource wrapper is often the first step in iterating on a fully-featured integration.
- **Reusable** Resources are a core building block in the Dagster ecosystem, and allow one to re-use code across assets.

### Cons

- **Low-level abstraction** While the resource can be re-used throughout the codebase, it does not provide any higher level abstraction to assets or jobs.

### Guide

:::note

A guide for writing a resource based integration is coming soon!

:::

## Factory methods

The factory pattern is used for creating multiple similar objects based on a set of specifications. This is often useful in the data engineering when you have similar processing that will operate on multiple objects with varying parameters.

For example, imagine you would like to perform an operation on a set of tables in a database. You could construct a factory method that takes in a table specification, resulting in a list of assets.

```python
from dagster import Definitions, asset

parameters = [
    {"name": "asset1", "table": "users"},
    {"name": "asset2", "table": "orders"},
]


def process_table(table_name: str) -> None:
    pass


def build_asset(params):
    @asset(name=params["name"])
    def _asset():
        process_table(params["table"])

    return _asset


assets = [build_asset(params) for params in parameters]

defs = Definitions(assets=assets)
```

### Pros

- **Flexibility:** Allows for fine-grained control over the integration logic.
- **Modularity:** Easy to reuse components across different assets and jobs.
- **Explicit configuration:** Resources can be explicitly configured, making it clear what dependencies are required.

### Cons

- **Complexity:** Can be more complex to set up compared to other methods.
- **Boilerplate code:** May require more boilerplate code to define assets, resources, and jobs.

### Guide

:::note

A guide for writing a factory method based integrations is coming soon!

:::

## Multi-asset decorators

In the scenario where a single API call or configuration can result in multiple assets, with a shared runtime or dependencies, one may consider creating a multi-asset decorator. Example implementations of this approach include [dbt](https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt), [dlt](https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dlt), and [Sling](https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/sling).

### Pros

- **Efficiency:** Allows defining multiple assets in a single function, reducing boilerplate code.
- **Simplicity:** Easier to manage related assets together.
- **Consistency:** Matches the the developer experience of the Dagster ecosystem by using decorator-based assets.

### Cons

- **Less granular control:** May not provide as much fine-grained control as defining individual assets.
- **Complexity in debugging:** Debugging issues can be more challenging when multiple assets are defined in a single function.

### Guide

- [Writing a multi-asset decorator integration](multi-asset-integration)

## Pipes protocol

The Pipes protocol is used to integrate with systems that have their own execution environments. It enables running code in these external environments while allowing Dagster to maintain control and visibility.

Example implementations of this approach include:
- [AWS Lambda](https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws/dagster_aws/pipes)
- [Databricks](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-databricks/dagster_databricks/pipes.py)
- [Kubernetes](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-k8s/dagster_k8s/pipes.py).

### Pros

- **Separation of Environments:** Allows running code in external environments, which can be useful for integrating with systems that have their own execution environments.
- **Flexibility:** Can integrate with a wide range of external systems and languages.
- **Streaming logs and metadata:** Provides support for streaming logs and structured metadata back into Dagster.

### Cons

- **Complexity:** Can be complex to set up and configure.
- **Overhead:** May introduce additional overhead for managing external environments.

### Guide

- [Dagster Pipes details and customization](/guides/build/external-pipelines/dagster-pipes-details-and-customization)
