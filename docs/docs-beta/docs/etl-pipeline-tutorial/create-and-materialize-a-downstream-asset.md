---
title: Create and materialize a downstream asset
description: Reference Assets as dependencies to other assets
last_update:
  author: Alex Noonan
sidebar_position: 30
---

Now that we have the raw data loaded into DuckDB, we need to create a [downstream asset](/guides/build/assets/defining-assets-with-asset-dependencies) that combines the upstream assets together. In this step, you will:

- Create a downstream asset
- Materialize that asset

## 1. Create a downstream asset

Now that we have all of our raw data loaded into DuckDB, our next step is to merge it together in a view composed of data from all three source tables.

To accomplish this in SQL, we will bring in our `sales_data` table and then left join on `sales_reps` and `products` on their respective id columns. Additionally, we will keep this view concise and only have relevant columns for analysis.

As you can see, the new `joined_data` asset looks a lot like our previous ones, with a few small changes. We put this asset into a different group. To make this asset dependent on the raw tables, we add the asset keys to the `deps` parameter in the asset definition.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="89" lineEnd="132"/>

## 2. Materialize the asset

1. Add the joined_data asset to the Definitions object

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

2. In the Dagster UI, reload definitions and materialize the `joined_data` asset.

## Next steps

- Continue this tutorial with by [creating and materializing a partitioned asset](ensure-data-quality-with-asset-checks).