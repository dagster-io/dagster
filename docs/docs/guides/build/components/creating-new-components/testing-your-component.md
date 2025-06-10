---
description: How to test components.
sidebar_position: 500
title: Testing your component
---

import DgComponentsRc from '@site/docs/partials/\_DgComponentsRc.md';

<DgComponentsRc />

## Testing custom components

After you [create a new component](/guides/build/components/creating-new-components/creating-and-registering-a-component), we recommend testing scaffolding and runtime execution with the Dagster framework utilities outlined below.

### The core workhorse: `scaffold_defs_sandbox`

The function at the core of our testing workflows is `scaffold_defs_sandbox`.

The function signature is the following:

```python
@contextmanager
def scaffold_defs_sandbox(
    *,
    component_cls: type,
    scaffold_params: Optional[dict[str, Any]] = None,
    component_path: Optional[Union[Path, str]] = None,
    scaffold_format: ScaffoldFormatOptions = "yaml",
    project_name: Optional[str] = None,
) -> Iterator[DefsPathSandbox]: ...
```

For the purposes of this guide, we will only concern ourselves with `component_cls` and `scaffold_params`. Users are highly unlikely to require the other parameters.

`scaffold_defs_sandbox` creates a lightweight sandbox to scaffold and instantiate a component in three steps:
1. Creates an empty folder structure (with an auto-generated project name and component path by default) that mimics the `defs/` folder portion of a real Dagster project. Practically speaking, this means a single folder at `src/<<project_name>>/defs/<<component_path>>` and which contains the scaffolded files within that leaf directory.
2. It then invokes the scaffolder on the component class in the context of that folder.
3. `scaffold_defs_sandbox` yields a `DefsPathSandbox` object, which you can program against.

Within the `with` block, you are free to assert facts about the scaffolded files.

For example, in our test of our Sling component (which scaffolds a `replication.yaml` file):

```python
def test_scaffold_sling():
    with scaffold_defs_sandbox(component_cls=SlingReplicationCollectionComponent) as defs_sandbox:
        assert (defs_sandbox.defs_folder_path / "defs.yaml").exists()
        assert (defs_sandbox.defs_folder_path / "replication.yaml").exists()
```

### DefsPathSandbox object

`scaffold_defs_sandbox` yields an object of type `DefsPathSandbox` as a context manager. You can use the object to load the component instance and the definitions it produces.

For example, the following is code from our tests of our [dlt component](/guides/build/components/integrations/dlt-component-tutorial) on already-created `DefsPathSandbox`. In this case, we ensure that the definitions have loaded, and that the correct asset keys have been created:

```python
with defs_sandbox.load() as (component, defs):
    assert isinstance(component, DltLoadCollectionComponent)
    assert len(component.loads) == 1
    assert defs.resolve_asset_graph().get_all_asset_keys() == {
        AssetKey(["example", "hello_world"]),
        AssetKey(["my_source_hello_world"]),
    }
```

However, that is just using the default `defs.yaml` file. Usually, you will want to customize the body of `defs.yaml`. For that, there is the `component_body` argument to `load`, demonstrated in the code that tests our `PythonScriptComponent`:

```python

def test_pipes_subprocess_script_hello_world() -> None:
    with scaffold_defs_sandbox(component_cls=PythonScriptComponent) as sandbox:
        # Create the script we will execute
        execute_path = sandbox.defs_folder_path / "script.py"
        execute_path.write_text("print('hello world')")

        # This will create a defs.yaml file in the sandboxed folder
        with sandbox.load(
            component_body={
                "type": "dagster.components.lib.executable_component.python_script_component.PythonScriptComponent",
                "attributes": {
                    "execution": {
                        "name": "op_name",
                        "path": "script.py",
                    },
                    "assets": [
                        {
                            "key": "asset",
                        }
                    ],
                },
            }
        ) as (component, defs):
            assert isinstance(component, PythonScriptComponent)
            assert isinstance(component.execution, ScriptSpec)

            # You can operate on definitions as normal
            assets_def = defs.get_assets_def("asset")
            result = materialize([assets_def])
            assert result.success
            mats = result.asset_materializations_for_node("op_name")
            assert len(mats) == 1
```
