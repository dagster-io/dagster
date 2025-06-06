---
title: 'Testing components'
description: How to test components.
sidebar_position: 600
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

After created components in your `defs` file you will want to test them. Components provides testing utilities that makes this simple.

The core function is `get_component_defs_within_project` that has the following signature:

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
    # This file is as my_project/tests/my_test.py so two parents up is the root
    project_root = Path(__file__).parent.parent
    return get_component_defs_within_project(project_root, component_path)
```

Once you do this you can load the component and its definitions. 

```python
def test_metadata() -> None:
    component, defs = my_project_component_defs("path/to/component")
```

The component instance is useful if you want to test that they appropriate metadata was created by yaml frontend. You can assert against whatever schema that component author has provided. 

With the `Definitions` object you can do actual execution against the definitions.