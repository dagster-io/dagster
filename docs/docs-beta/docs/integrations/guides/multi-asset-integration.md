---
title: Creating a multi-asset integration
description: Create a decorator based multi-asset integration
sidebar_position: 200
---

When working in the Dagster ecosystem, you may have noticed that decorators are frequently used. For example, assets, jobs, and ops use decorators. If you have a service that produces many assets, it's possible to define it as a multi-asset decorator-offering a consistent and intuitive developer experience to existing Dagster APIs.

In the context of Dagster, decorators are helpful because they often wrap some form of processing. For example, when writing an asset, you define your processing code and then annotate the function with the `asset` decorator /> decorator. Then, the internal Dagster code can register the asset, assign metadata, pass in context data, or perform any other variety of operations that are required to integrate your asset code with the Dagster platform.

In this guide, you'll learn how to develop a multi-asset integration for a hypothetical replication tool.

:::note
This guide assumes basic familiarity with Dagster and Python decorators.
:::

## Step 1: Input

For this guide, let's imagine a tool that replicates data between two databases. It's configured using a `replication.yaml` configuration file, in which a user is able to define source and destination databases, along with the tables that they would like to replicate between these systems.

```yml
connections:
  source:
    type: duckdb
    connection: example.duckdb
  destination:
    type: postgres
    connection: postgresql://postgres:postgres@localhost/postgres

tables:
  - name: users
    primary_key: id
  - name: products
    primary_key: id
  - name: activity
    primary_key: id
```

For the integration we're building, we want to provide a multi-asset that encompasses this replication process, and generates an asset for each table being replicated.

We will define a dummy function named `replicate` that will mock the replication process, and return a dictionary with the replication status of each table. In the real world, this could be a function in a library, or a call to a command-line tool.

```python
import yaml

from pathlib import Path
from typing import Mapping, Iterator, Any


def replicate(replication_configuration_yaml: Path) -> Iterator[Mapping[str, Any]]:
    data = yaml.safe_load(replication_configuration_yaml.read_text())
    for table in data.get("tables"):
        # < perform replication here, and get status >
        yield {"table": table.get("name"), "status": "success"}
```

## Step 2: Implementation

First, let's define a `Project` object that takes in the path of our configuration YAML file. This will allow us to encapsulate the logic that gets metadata and table information from our project configuration.

```python
import yaml
from pathlib import Path


class ReplicationProject():
    def __init__(self, replication_configuration_yaml: str):
        self.replication_configuration_yaml = replication_configuration_yaml

    def load(self):
        return yaml.safe_load(Path(self.replication_configuration_yaml).read_text())
```

Next, define a function that returns a `multi_asset` function. The `multi_asset` function is a decorator itself, so this allows us to customize the behavior of `multi_asset` and create a new decorator of our own:

```python
def custom_replication_assets(
    *,
    replication_project: ReplicationProject,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    project = replication_project.load()

    return multi_asset(
        name=name,
        group_name=group_name,
        specs=[
            AssetSpec(
                key=table.get("name"),
            )
            for table in project.get("tables")
        ],
    )
```

Let's review what this code does:

- Defines a function that returns a `multi_asset` function
- Loads our replication project and iterates over the tables defined in the input YAML file
- Uses the tables to create a list of `AssetSpec` objects and passes them to the `specs` parameter, thus defining assets that will be visible in the Dagster UI

Next, we'll show you how to perform the execution of the replication function.

Recall that decorators allow us to wrap a function that performs some operation. In the case of our `multi_asset`, we defined `AssetSpec` objects for our tables, and the actual processing that takes place will be in the body of the decorated function.

In this function, we will perform the replication, and then yield `AssetMaterialization` objects indicating that the replication was successful for a given table.

```python
from dagster import AssetExecutionContext


replication_project_path = "replication.yaml"
replication_project = ReplicationProject(replication_project_path)


@custom_replication_assets(
    replication_project=replication_project,
    name="my_custom_replication_assets",
    group_name="replication",
)
def my_assets(context: AssetExecutionContext):
    results = replicate(Path(replication_project_path))
    for table in results:
        if table.get("status") == "SUCCESS":
            yield AssetMaterialization(asset_key=str(table.get("name")), metadata=table)
```

There are a few limitations to this approach:

- **We have not encapsulated the logic for replicating tables.** This means that users who use the `custom_replication_assets` decorator would be responsible for yielding asset materializations themselves.
- **Users can't customize the attributes of the asset**.

For the first limitation, we can resolve this by refactoring the code in the body of our asset function into a Dagster resource.

## Step 3: Moving the replication logic into a resource

Refactoring the replication logic into a resource enables us to support better configuration and re-use of our logic.

To accomplish this, we will extend the `ConfigurableResource` object to create a custom resource. Then, we will define a `run` method that will perform the replication operation:

```python
from dagster import ConfigurableResource
from dagster._annotations import public


class ReplicationResource(ConfigurableResource):
    @public
    def run(
        self, replication_project: ReplicationProject
    ) -> Iterator[AssetMaterialization]:
        results = replicate(Path(replication_project.replication_configuration_yaml))
        for table in results:
            if table.get("status") == "SUCCESS":
                # NOTE: this assumes that the table name is the same as the asset key
                yield AssetMaterialization(
                    asset_key=str(table.get("name")), metadata=table
                )
```

Now, we can refactor our `custom_replication_assets` instance to use this resource:

```python
@custom_replication_assets(
    replication_project=replication_project,
    name="my_custom_replication_assets",
    group_name="replication",
)
def my_assets(replication_resource: ReplicationProject):
    replication_resource.run(replication_project)
```

## Step 4: Using translators

At the end of [Step 2](#step-2-implementation), we mentioned that end users were unable to customize asset attributes, like the asset key, generated by our decorator. Translator classes are the recommended way of defining this logic, and they provide users with the option to override the default methods used to convert a concept from your tool (for example, a table name) to the corresponding concept in Dagster (for example, asset key).

To start, we will define a translator method to map the table specification to a Dagster asset key.

:::note
In a real world integration, you will want to define methods for all common attributes like dependencies, group names, and metadata.
:::

```python
from dagster import AssetKey, _check as check

from dataclasses import dataclass


@dataclass
class ReplicationTranslator:
    @public
    def get_asset_key(self, table_definition: Mapping[str, str]) -> AssetKey:
        return AssetKey(str(table_definition.get("name")))
```

Next, we'll update `custom_replication_assets` to use the translator when defining the `key` on the `AssetSpec`. 

:::note
Note that we took this opportunity to also include the replication project and translator instance on the `AssetSpec` metadata. This is a workaround that we tend to employ in this approach, as it makes it possible to define these objects once and then access them on the context of our asset.
:::

```python
def custom_replication_assets(
    *,
    replication_project: ReplicationProject,
    name: Optional[str] = None,
    group_name: Optional[str] = None,
    translator: Optional[ReplicationTranslator] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    project = replication_project.load()

    translator = (
        check.opt_inst_param(translator, "translator", ReplicationTranslator)
        or ReplicationTranslator()
    )

    return multi_asset(
        name=name,
        group_name=group_name,
        specs=[
            AssetSpec(
                key=translator.get_asset_key(table),
                metadata={
                    "replication_project": project,
                    "replication_translator": translator,
                },
            )
            for table in project.get("tables")
        ],
    )
```

Finally, we have to update our resource to use the translator and project provided in the metadata. We are using the `check` method provided by `dagster._check` to ensure that the type of the object is appropriate as we retrieve it from the metadata.

Now, we can use the same `translator.get_asset_key` when yielding the asset materialization, thus ensuring that our asset declarations match our asset materializations:

```python
class ReplicationResource(ConfigurableResource):
    @public
    def run(self, context: AssetExecutionContext) -> Iterator[AssetMaterialization]:
        metadata_by_key = context.assets_def.metadata_by_key
        first_asset_metadata = next(iter(metadata_by_key.values()))

        project = check.inst(
            first_asset_metadata.get("replication_project"),
            ReplicationProject,
        )

        translator = check.inst(
            first_asset_metadata.get("replication_translator"),
            ReplicationTranslator,
        )

        results = replicate(Path(project.replication_configuration_yaml))
        for table in results:
            if table.get("status") == "SUCCESS":
                yield AssetMaterialization(
                    asset_key=translator.get_asset_key(table), metadata=table
                )
```

## Conclusion

In this guide we walked through how to define a custom multi-asset decorator, a resource for encapsulating tool logic, and a translator for defining the logic to translate a specification to Dagster concepts.

Defining integrations with this approach aligns nicely with the overall development paradigm of Dagster, and is suitable for tools that generate many assets.

The code in its entirety can be seen below:

<CodeExample filePath="guides/tutorials/multi-asset-integration/integration.py" language="python" />
