---
title: 'Lesson 3: Creating a Dagster resource to run dbt'
module: 'dagster_dbt'
lesson: '3'
---

# Creating a Dagster resource to run dbt

Our next step is to define a Dagster resource as the entry point used to run dbt commands and configure its execution.

The `DbtCliResource` is the main resource that you’ll be working with. In later sections, we’ll walk through some of the resource’s methods and how to customize what Dagster does when dbt runs.

{% callout %}

> 💡 **Resource refresher:** Resources are Dagster’s recommended way of connecting to other services and tools, such as dbt, your data warehouse, or a BI tool.
> {% /callout %}

Navigate to the `dagster_university/resources/__init__.py`, which is where other resources are defined. Copy and paste the following code to their respective locations:

```python
from dagster_dbt import DbtCliResource

from ..project import dbt_project
# the import lines go at the top of the file

# this can be defined anywhere below the imports
dbt_resource = DbtCliResource(
    project_dir=dbt_project,
)
```

The code above:

1. Imports the `DbtCliResource` from the `dagster_dbt` package that we installed earlier
2. Imports the `dbt_project` representation we just defined
3. Instantiates a new `DbtCliResource` under the variable name `dbt_resource`
4. Tells the resource that the dbt project to execute is the `dbt_project`
