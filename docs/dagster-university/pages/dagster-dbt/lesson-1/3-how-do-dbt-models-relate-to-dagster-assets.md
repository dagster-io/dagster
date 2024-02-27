---
title: "Lesson 1: How do dbt models relate to Dagster assets?"
module: 'dbt_dagster'
lesson: '1'
---

# How do dbt models relate to Dagster assets?

dbt models _are_ assets: they produce data and can have dependencies. Because of these similarities, Dagster can translate each of your dbt models into a Dagster [Software-defined Asset](https://docs.dagster.io/concepts/assets/software-defined-assets) (SDA).

How can Dagster do this? Each component of a Dagster asset has an equivalent counterpart in a dbt model:

- The **asset key** for a dbt model is (by default) the name of the model
- The **upstream dependencies** of a dbt model are defined with **`ref`** or **`source`** calls within the model's definition
- The **computation** required to compute the asset from its upstream dependencies is the SQL within the model's definition

These similarities make it natural to interact with dbt models as Dagster assets. Using dbt with Dagster, you can create an asset graph like the following:

![Dagster graph with dbt, Fivetran, and TensorFlow](/images/dagster-dbt/lesson-1/example-asset-graph.png)

From code like this:

```python file=/integrations/dbt/potemkin_dag_for_cover_image.py startafter=start endbefore=end
from pathlib import Path

from dagster_dbt import DbtCliResource, dbt_assets, get_asset_key_for_model
from dagster_fivetran import build_fivetran_assets

from dagster import AssetExecutionContext, asset

fivetran_assets = build_fivetran_assets(
    connector_id="postgres",
    destination_tables=["users", "orders"],
)


@dbt_assets(manifest=Path("manifest.json"))
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    compute_kind="tensorflow",
    deps=[get_asset_key_for_model([dbt_project_assets], "daily_order_summary")],
)
def predicted_orders():
    ...
```

Let's break down what's happening in this example:

- Using `build_fivetran_assets`, we load two tables (`users`, `orders`) from a Fivetran Postgres connector as Dagster assets
- Using `@dbt_assets`, Dagster reads from a dbt project's `manifest.json` and creates Dagster assets from the dbt models it finds
- Lastly, we create a Dagster `@asset` named `predicted_orders` that has an upstream dependency on a dbt asset named `daily_order_summary`
