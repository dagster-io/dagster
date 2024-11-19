---
title: Creating a Downstream Asset
description: Reference Assets as dependencies to other assets
last_update:
  author: Alex Noonan
---

# Asset Dependencies

Now that we have the raw data loaded into DuckDB, we need to create a [downstream asset](guides/asset-dependencies.md) that combines the staging assets together. In this step, you will:

- Create a downstream asset
- Materialize that asset

## Creating a Downstream asset

Now that we have all of our raw data loaded and staged into DuckDB our next step is to merge it together in a .

The data structure that of a fact table (sales data) with 2 dimensions off of it (sales reps and products). To accomplish that in SQL we will bring in our `sales_data` table and then left join on `sales_reps` and `products` on their respective id columns. Additionally, we will keep this view concise and only have relevant columns for analysis.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="89" lineEnd="132"/>

As you can see here this asset looks a lot like our previous ones with a few small changes. We put this asset into a different group. To make this asset dependent on the raw tables we add the asset keys the `deps` parameter in the asset definition.

## Materialize the Asset

We need to add the Asset we just made to the Definitions object.

Your Definitions object should now look like this:

  ```python
  defs = dg.Definitions(
    assets=[products,
        sales_reps,
        sales_data,
        joined_data,
    ],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  )
  ```

Go back into the UI, reload definitions, and materialize the `joined_data` asset.

## Next steps

- Continue this tutorial by adding [asset checks](/tutorial/04-ensuring-data-quality-with-asset-checks)