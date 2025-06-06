---
title: 'Testing components'
description: How to test components.
sidebar_position: 600
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

After creating components in your `defs` folder you will want to test them. Components provides testing utilities that makes this simple.

The core function is `get_component_defs_within_project` and it has the following signature:

```python
def get_component_defs_within_project(
    *,
    project_root: Union[str, Path],
    component_path: Union[str, Path],
    instance_key: int = 0,
) -> tuple[Component, Definitions]:
```

`project_root` is the root of the project, typically the folder that contains `pyproject.toml` or `setup.py`. In test cases it is very convenient to setup a lightweight wrapper so you only have to set the project root once:

```python
def my_project_component_defs(component_path) -> tuple[dg.Component, dg.Definitions]:
    # This file is as my_project/tests/my_test.py so two parents up from the test file 
    project_root = Path(__file__).parent.parent
return get_component_defs_within_project(project_root=project_root, component_path=component_path)
```

Once you do this you can load the component and its definitions. This component lives at `my_project/src/my_project/defs/path/to/component`. You only need to specify the path relative to the `defs` folder.

```python
def test_metadata() -> None:
    component, defs = my_project_component_defs("path/to/component")
```

The component instance is useful if you want to test that the appropriate metadata was created by yaml frontend. You can assert against whatever schema that component author has provided. 

For example if you are creating a `FunctionComponent` you may want to assert facts about its assets:

```python
def test_function_component_metadata() -> None:
    component, defs = my_project_component_defs("path/to/function_component")
    assert isinstance(component, dg.FunctionComponent)
    assert len(component.assets) == 1
    assert component.assets[0] == dg.AssetKey("some_asset")
```

With the `Definitions` object you can do actual execution against the definitions

```python
def test_function_component_execution() -> None:
    component, defs = my_project_component_defs("path/to/function_component")
    assert dg.materialize(defs.get_assets_def("some_asset")).success
```

See (some link) for more information about testing definitions.