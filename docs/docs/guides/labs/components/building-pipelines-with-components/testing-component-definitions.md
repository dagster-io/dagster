---
title: 'Testing component definitions'
description: How to test component definitions.
sidebar_position: 600
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

After creating components in your `defs` folder, you will want to test them. Dagster provides testing utilities that makes testing components simple.

The core function is `get_component_defs_within_project` and it has the following signature:

```python
def get_component_defs_within_project(
    *,
    project_root: Union[str, Path],
    component_path: Union[str, Path],
    instance_key: int = 0,
) -> tuple[Component, Definitions]:
```

:::note

`project_root` is the root of the project, typically the folder that contains `pyproject.toml` or `setup.py`. 

:::

## Create wrapper function

In your test file, it is very convenient to set up a lightweight wrapper function so you only have to set the project root once:

```python title="my-project/tests/my_test.py"
def my_project_component_defs(component_path) -> tuple[dg.Component, dg.Definitions]:
    # Project root is two parents up from the test file 
    project_root = Path(__file__).parent.parent
return get_component_defs_within_project(project_root=project_root, component_path=component_path)
```

Once you do this, you can load the component and its definitions. This component lives at `my-project/src/my_project/defs/path/to/component`. You only need to specify the path relative to the `defs` folder:

```python title="my-project/tests/my_test.py"
def test_metadata() -> None:
    component, defs = my_project_component_defs("path/to/component")
```

## Testing metadata

The `component` instance is useful if you want to test that the appropriate metadata was created by the YAML frontend. You can assert against the schema that the component author has provided. 

For example, if you are using a `FunctionComponent` in your project, you may want to assert facts about its assets:

```python title="my-project/tests/my_test.py"
def test_function_component_metadata() -> None:
    component, defs = my_project_component_defs("path/to/function_component")
    assert isinstance(component, dg.FunctionComponent)
    assert len(component.assets) == 1
    assert component.assets[0] == dg.AssetKey("some_asset")
```

## Test component definition execution

With the `Definitions` object, you can do actual execution against the component definitions:

```python title="my-project/tests/my_test.py"
def test_function_component_execution() -> None:
    component, defs = my_project_component_defs("path/to/function_component")
    assert dg.materialize(defs.get_assets_def("some_asset")).success
```

See (some link) for more information about testing definitions.