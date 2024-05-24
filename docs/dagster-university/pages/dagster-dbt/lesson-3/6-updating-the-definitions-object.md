---
title: 'Lesson 3: Updating the Definitions object'
module: 'dagster_dbt'
lesson: '3'
---

# Updating the Definitions object

The last step in setting up your dbt project in Dagster is adding the definitions you made (ex. your `dbt_resource` and `dbt_analytics` asset) to your code location’s `Definitions` object.

Modify your root-level `__init__.py` to:

- Load assets from `dbt.py` file, and
- Register the `dbt_resource` from `.resources` under the resource key `dbt`

After making those changes, your root-level `__init__.py` should look like similar to below:

```python
from dagster import Definitions, load_assets_from_modules

from .assets import trips, metrics, requests, dbt # Import the dbt assets
from .resources import database_resource, dbt_resource # import the dbt resource
# ...other existing imports

# ... existing calls to load_assets_from_modules
dbt_analytics_assets = load_assets_from_modules(modules=[dbt]) # Load the assets from the file

# ... other declarations

defs = Definitions(
    assets=[*trip_assets, *metric_assets, *requests_assets, *dbt_analytics_assets], # Add the dbt assets to your code location
    resources={
        "database": database_resource,
        "dbt": dbt_resource # register your dbt resource with the code location
    },
  # .. other definitions
)
```
