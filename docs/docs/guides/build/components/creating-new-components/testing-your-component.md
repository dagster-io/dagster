---
description: Best practices for testing components you have created.
sidebar_position: 500
title: Testing custom components
---

After you [create a new component](/guides/build/components/creating-new-components/creating-and-registering-a-component), we recommend testing scaffolding and runtime execution with the Dagster framework utilities outlined below.

## Setting up a sandbox

The function at the core of our testing workflows is <PyObject section="components" module="dagster" object="components.testing.create_defs_folder_sandbox" displayText="create_defs_folder_sandbox" />. This context manager allows you to construct a temporary `defs` folder, which can be populated with components and loaded into Component objects, or built into dagster <PyObject section="definitions" module="dagster" object="Definitions" /> just as they would be in a real Dagster project. It then yields a <PyObject section="components" module="dagster" object="components.testing.DefsFolderSandbox" displayText="DefsFolderSandbox" /> object that can be used to scaffold and load components.

Once created, the <PyObject section="components" module="dagster" object="components.testing.DefsFolderSandbox" displayText="DefsFolderSandbox" /> object provides a number of useful utilities for scaffolding and loading components:

* <PyObject section="components" module="dagster" object="components.testing.DefsFolderSandbox.scaffold_component" displayText="scaffold_component" /> to scaffold a component into the `defs` folder.
* <PyObject section="components" module="dagster" object="components.testing.DefsFolderSandbox.load_component_and_build_defs" displayText="load_component_and_build_defs" /> to test instantiation of a component, and to validate the definitions it produces.

### Scaffolding a component

The <PyObject section="components" module="dagster" object="components.testing.DefsFolderSandbox.scaffold_component" displayText="scaffold_component" /> method allows you to scaffold a component into the `defs` folder, just as a user would using the `dg scaffold defs <COMPONENT_NAME>` CLI command.

The only required parameter is `component_cls`, which is the class of the component to scaffold. Without providing any other parameters, this will scaffold a YAML component with a random name and default contents. Other parameters allow you to simulate passing parameters to the scaffolding CLI command, or to specify a specific path for the newly created component.

This can be used to verify the behavior of a custom scaffolder. Here is an example of use in our test of our [Sling component](/integrations/libraries/sling) (which scaffolds a `replication.yaml` file):

```python
def test_scaffold_sling():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=SlingReplicationCollectionComponent)
        assert (defs_path / "defs.yaml").exists()
        assert (defs_path / "replication.yaml").exists()
```

For ease of use, the `defs_yaml_contents` argument can be used to replace the contents of the `defs.yaml` file after the component has been scaffolded.

### Loading and building definitions

To test instantiation of a component, and to validate the definitions it produces, you can use the <PyObject section="components" module="dagster" object="components.testing.DefsFolderSandbox.load_component_and_build_defs" displayText="load_component_and_build_defs" /> method, which loads an already-scaffolded component and builds the corresponding Definitions.

For example, the following is code from our [dlt component](/integrations/libraries/dlt) tests. In this case, we ensure that the definitions have loaded, and that the correct asset keys have been created:

```python
def test_dlt_component():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=DltLoadCollectionComponent)
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, DltLoadCollectionComponent)
            assert len(component.loads) == 1
            assert defs.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["example", "hello_world"]),
                AssetKey(["my_source_hello_world"]),
            }
```

## Testing multiple components

These utilities are also useful for testing multiple components in a single test. For example, testing the `TemplatedSqlComponent` with a Snowflake connection:

```python
def test_snowflake_component():
    with create_defs_folder_sandbox() as sandbox:
        sandbox.scaffold_component(
            component_cls=SqlComponent,
            defs_path="sql_execution_component",
            defs_yaml_contents={
                "type": "dagster.TemplatedSqlComponent",
                "attributes": {
                    "sql_template": "SELECT * FROM MY_TABLE;",
                    "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
                    "connection": "{{ load_component_at_path('sql_connection_component') }}",
                },
            },
        )

        sandbox.scaffold_component(
            component_cls=SnowflakeConnectionComponent,
            defs_path="sql_connection_component",
            defs_yaml_contents={
                "type": "dagster_snowflake.SnowflakeConnectionComponent",
                "attributes": {
                    "account": "test_account",
                    "user": "test_user",
                    "password": "test_password",
                    "database": "TESTDB",
                    "schema": "TESTSCHEMA",
                },
            },
        )

        with sandbox.build_all_defs() as defs:
            assert defs.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
            }
```
