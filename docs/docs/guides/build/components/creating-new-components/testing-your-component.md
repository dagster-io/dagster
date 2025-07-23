---
description: How to test components.
sidebar_position: 500
title: Testing your component
---

## Testing custom components

After you [create a new component](/guides/build/components/creating-new-components/creating-and-registering-a-component), we recommend testing scaffolding and runtime execution with the Dagster framework utilities outlined below.

### Setting up a sandbox with `temp_components_sandbox`

The function at the core of our testing workflows is `dagster.components.testing.temp_components_sandbox`. This context manager allows you to construct a temporary defs folder, which can be populated with components and loaded into Component objects or built into dagster Definitions just as they would be in a real Dagster project.

The function signature is the following:

```python
@contextmanager
def temp_components_sandbox(
    *,
    project_name: Optional[str] = None,
) -> Iterator[DefsSandbox]: ...
```

### The `DefsSandbox` object

Once created, the `DefsSandbox` object provides a number of useful utilities for scaffolding and loading components.

#### Creating a component with `scaffold_component`

The `scaffold_component` method allows you to scaffold a component into the defs folder, just as a user would using the `dg scaffold component` CLI command.

The signature is

```python
def scaffold_component(
    self,
    component_cls: Any,
    component_path: Optional[Union[Path, str]] = None,
    scaffold_params: Optional[dict[str, Any]] = None,
    scaffold_format: ScaffoldFormatOptions = "yaml",
    component_body: Optional[dict[str, Any]] = None,
) -> Path: ...
```

The only required parameter is `component_cls`, which is the class of the component to scaffold - without providing any other parameters, this will scaffold a YAML component with a random name and default contents. Other parameters allow you to simulate passing parameters to the scaffolding CLI command, or to specify a specific path for the newly created component.

This can be used to verify the behavior of a custom scaffolder. Here is an example of use in our test of our Sling component (which scaffolds a `replication.yaml` file):

```python
def test_scaffold_sling():
    with temp_components_sandbox() as sandbox:
        component_path = sandbox.scaffold_component(component_cls=SlingReplicationCollectionComponent)
        assert (component_path / "defs.yaml").exists()
        assert (component_path / "replication.yaml").exists()
```

For ease of use, the `component_body` argument can be used to replace the contents of the `defs.yaml` file after the component has been scaffolded.

#### Loading and building definitions with `load_component_and_build_defs_at_path`

To test instantiation of a component, and to validate the definitions it produces, you can use the `load_component_and_build_defs_at_path` method, which loads an already-scaffolded component and builds the corresponding Definitions.

For example, the following is code from our tests of our [dlt component](/guides/build/components/integrations/dlt-component-tutorial). In this case, we ensure that the definitions have loaded, and that the correct asset keys have been created:

```python
def test_dlt_component():
    with temp_components_sandbox() as defs_sandbox:
        component_path = defs_sandbox.scaffold_component(component_cls=DltLoadCollectionComponent)
        with defs_sandbox.load_component_and_build_defs_at_path(component_path=component_path) as (
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

#### Scaffolding and building definitions in a single invocation with `scaffold_load_and_build_component_defs`

The `DefsSandbox` object also provides a convenience method for creating a new component with custom `defs.yaml` contents and building the corresponding Definitions.
This is the easiest way to test a fully configured component, such as the Fivetran component:

```python
def test_fivetran_component():
    with temp_components_sandbox() as defs_sandbox:
        with defs_sandbox.scaffold_load_and_build_component_defs(
            component_cls=FivetranAccountComponent,
            component_body={
                "type": "dagster_fivetran.FivetranAccountComponent",
                "attributes": {
                    "workspace": {
                        "api_key": "{{ env.FIVETRAN_API_KEY }}",
                        "api_secret": "{{ env.FIVETRAN_API_SECRET }}",
                        "account_id": "{{ env.FIVETRAN_ACCOUNT_ID }}",
                    },
                }
            },
        ) as (component, defs):
            assert isinstance(component, FivetranAccountComponent)
```


#### Testing multiple components

These utilities are also useful for testing multiple components in a single test. For example, testing the `TemplatedSqlComponent` with a Snowflake connection:

```python
def test_snowflake_component():
    with temp_components_sandbox() as sandbox:
        sandbox.scaffold_component(
            component_cls=SqlComponent,
            component_path="sql_execution_component",
            component_body={
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
            component_path="sql_connection_component",
            component_body={
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
