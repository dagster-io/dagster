---
description: How to test components.
sidebar_position: 500
title: Testing your component
---

## Testing custom components

After you [create a new component](/guides/build/components/creating-new-components/creating-and-registering-a-component), we recommend testing scaffolding and runtime execution with the Dagster framework utilities outlined below.

### Setting up a sandbox with `create_defs_folder_sandbox`

The function at the core of our testing workflows is `dagster.components.testing.create_defs_folder_sandbox`. This context manager allows you to construct a temporary defs folder, which can be populated with components and loaded into Component objects or built into dagster Definitions just as they would be in a real Dagster project.

The function signature is the following:

```python
@contextmanager
def create_defs_folder_sandbox(
    *,
    project_name: Optional[str] = None,
) -> Iterator[DefsFolderSandbox]: ...
```

### The `DefsFolderSandbox` object

Once created, the `DefsFolderSandbox` object provides a number of useful utilities for scaffolding and loading components.

#### Creating a component with `scaffold_component`

The `scaffold_component` method allows you to scaffold a component into the defs folder, just as a user would using the `dg scaffold component` CLI command.

The signature is

```python
def scaffold_component(
    self,
    component_cls: Any,
    defs_path: Optional[Union[Path, str]] = None,
    scaffold_params: Optional[dict[str, Any]] = None,
    scaffold_format: ScaffoldFormatOptions = "yaml",
    defs_yaml_contents: Optional[dict[str, Any]] = None,
) -> Path: ...
```

The only required parameter is `component_cls`, which is the class of the component to scaffold - without providing any other parameters, this will scaffold a YAML component with a random name and default contents. Other parameters allow you to simulate passing parameters to the scaffolding CLI command, or to specify a specific path for the newly created component.

This can be used to verify the behavior of a custom scaffolder. Here is an example of use in our test of our Sling component (which scaffolds a `replication.yaml` file):

```python
def test_scaffold_sling():
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(component_cls=SlingReplicationCollectionComponent)
        assert (defs_path / "defs.yaml").exists()
        assert (defs_path / "replication.yaml").exists()
```

For ease of use, the `defs_yaml_contents` argument can be used to replace the contents of the `defs.yaml` file after the component has been scaffolded.

#### Loading and building definitions with `load_component_and_build_defs`

To test instantiation of a component, and to validate the definitions it produces, you can use the `load_component_and_build_defs` method, which loads an already-scaffolded component and builds the corresponding Definitions.

For example, the following is code from our tests of our [dlt component](/integrations/libraries/dlt). In this case, we ensure that the definitions have loaded, and that the correct asset keys have been created:

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

#### Testing multiple components

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
