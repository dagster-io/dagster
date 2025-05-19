---
title: 'Testing components'
description: How to test components.
sidebar_position: 500
unlisted: true
---

## Testing component definitions in projects

Once you have created a project and created definitions in that project, you will want to be able to test it.

Components comes with testing utilities to make this as easy as possible.

`build_component_at_defs_path` and `build_component_defs_at_defs_path` are the workhouse functions here.

```python
from dagster.components import ComponentLoadContext
from dagster.components.test import get_project_root

def test_component() -> None:
    context = ComponentLoadContext.for_project_root(get_project_root(__file__))

    component = build_component_at_defs_path(context, defs_path="path/to/module")

    # assert properties of the component here. Can test the yaml frontend before loading definitions

    defs = build_component_defs_at_defs_path(context, defs_path="path/to/module")

    # assert properties

```

## Testing custom componets