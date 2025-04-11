---
title: 'Using resources in dg projects'
sidebar_position: 250 
---

Assets, asset checks, and sensors in Dagster frequently require resources that are instantiated elsewhere in the project. 

For example you have an asset:

```python
# src/defs/asset_one.py
import dagster as dg
from my_project.resources import AResource

@dg.asset
def asset_one(a_resource: AResource): ...
```

And a separately defined resource at the root of the project:

```python
# src/resources.py
import dagster as dg

class AResource(dg.ConfigurableResource): ...
```

Resources can be added at any level in the `defs` hierarchy by creating a `Definitions` object.

```python
# src/defs/resources.py
import dagster as dg
from resource_docs.resources import AResource

defs = dg.Definitions(
    resources={"a_resource": AResource(name="foo")},
)
```

Resource binding can happen at any level of the hierarchy. Which means that if you moved `asset_one` in this example to be in a subdirectory, you could leave the existing `resources.py` file at `src/defs/resources.py`.

```
src
└── resource_docs
    ├── definitions.py
    ├── defs
    │   ├── assets
    │   │   └── asset_one.py # contains def asset_one():
    │   └── resources.py # contains AResource()
    └── resources.py # contains class AResource
```