---
title: Asset Dependencies and Checks
description: Reference Assets as dependencies to other assets and asset checks. 
last_update:
  date: 2024-10-16
  author: Alex Noonan
---

# Asset Dependencies and Asset Checks

The DAG or Directed Acyclic Graph is a key part of Dagster. This is an improvement over the typical cron workflow for orchestration. With a Dag approach you can easily understand complex data pipelines. The key benefits of Dags are

1. Clarity: The DAG provides a clear visual representation of the entire workflow.
2. Efficiency: Parallel tasks can be identified and executed simultaneously.
3. Reliability: Dependencies ensure that tasks are executed in the correct order.
4. Scalability: Complex workflows can be managed effectively.
5. Maintenance: It's easier to update or troubleshoot specific parts of the workflow.

## What you'll learn

- Creating [Asset Dependencies](guides/asset-dependencies.md) 
- How to make an [Asset Check](guides/asset-checks.md)

## Creating a Downstream asset

Now that we have all of our raw data loaded and staged into the DuckDB database our next step is to merge it together. The data structure that of a fact table (sales data) with 2 dimensions off of it (sales reps and products). To accomplish that in SQL we will bring in our sales_data table and then left join on sales reps and products on their respective id columns. Additionally, we will keep this view concise and only have relevant columns for analysis.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="89" lineEnd="132"/>

As you can see here this asset looks a lot like our previous ones with a few small changes. We put this asset into a different group. To make this asset dependant on the raw tables we add the asset keys the `deps` parameter in the asset definition.  

## Asset checks

Data Quality is critical in analytics. Just like in a factory producing cars, manufacturers inspect parts after they complete steps to identify defects and processes that may be creating more than acceptable. In this case we want to create a test to identify if there are any rows that have a product or sales rep that are not in the table. 

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="134" lineEnd="149"/>


## Materialize the Assets

We need to add the asset and asset check we just made to the definitions object. 

Your Definitions object should now look like this:

  ```python 
  defs = dg.Definitions(
    assets=[products,
        sales_reps,
        sales_data,
        joined_data,
    ],
    asset_checks=[missing_dimension_check],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
  )
  ```

Go back into the UI, reload definitions, and materialize the joined_data asset. If you navigate to the asset details page, there is tab for asset checks where you can see the run history and metadata. 

  ![2048 resolution](/images/tutorial/etl-tutorial/asset-check.png)

## What you've learned

- Creating downstream assets
- Software defined asset checks. 


## Next steps

- Continue this tutorial with your [Partitions](/tutorial/04-partitions)