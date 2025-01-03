---
title: Create and Materialize Partitioned Assets
description: Partitioning Assets by datetime and categories
last_update:
  date: 2024-11-25
  author: Alex Noonan
sidebar_position: 50
---

[Partitions](/guides/build/create-a-pipeline/partitioning) are a core abstraction in Dagster, they are how you manage large datasets, process incremental updates, and improve pipeline performance. In Dagster you can partition assets the following ways:

1. Time-based: Split data by time periods (e.g., daily, monthly)
2. Category-based: Divide by known categories (e.g., country, product type)
3. Two-dimensional: Combine two partition types (e.g., country + date)
4. Dynamic: Create partitions based on runtime conditions

In this step you will:

- Create an asset that is partitioned by month
- Create an asset that is partitioned by defined categories

## 1. Create a time based partitioned asset

Partitioning by datetime groups is supported in Dagster natively. We want to create an asset that calculates the monthly performance for each sales rep. To create the monthly partition copy the following code below the `missing_dimension_check` asset check.

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="152" lineEnd="153"/>

Partition data are accessed within an asset by context. We want to create an asset that does this calculation for a given month from the partition and deletes any previous value for that month. Paste the following asset under the `monthly_partition` we just created

  ```python
  @dg.asset(
      partitions_def=monthly_partition,
      compute_kind="duckdb",
      group_name="analysis",
      deps=[joined_data],
  )
  def monthly_sales_performance(
      context: dg.AssetExecutionContext, duckdb: DuckDBResource
  ):
      partition_date_str = context.partition_key
      month_to_fetch = partition_date_str[:-3]

      with duckdb.get_connection() as conn:
          conn.execute(
              f"""
              create table if not exists monthly_sales_performance (
                  partition_date varchar,
                  rep_name varchar,
                  product varchar,
                  total_dollar_amount double
              );

              delete from monthly_sales_performance where partition_date = '{month_to_fetch}';

              insert into monthly_sales_performance
              select
                  '{month_to_fetch}' as partition_date,
                  rep_name, 
                  product_name,
                  sum(dollar_amount) as total_dollar_amount
              from joined_data where strftime(date, '%Y-%m') = '{month_to_fetch}'
              group by '{month_to_fetch}', rep_name, product_name;
              """
          )

          preview_query = f"select * from monthly_sales_performance where partition_date = '{month_to_fetch}';"
          preview_df = conn.execute(preview_query).fetchdf()
          row_count = conn.execute(
              f"""
              select count(*)
              from monthly_sales_performance
              where partition_date = '{month_to_fetch}'
              """
          ).fetchone()
          count = row_count[0] if row_count else 0

      return dg.MaterializeResult(
          metadata={
              "row_count": dg.MetadataValue.int(count),
              "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
          }
      )
  ```

## 2. Create a statically partitioned asset

Using known defined partitions is a simple way to break up your dataset when you know the different groups you want to subset it by. In our pipeline we want to create a an asset that is the performance of each product category. 

1. To create the static defined partition for the product category paste this code beneath the `monthly_sales_performance` asset:

<CodeExample filePath="guides/tutorials/etl_tutorial/etl_tutorial/definitions.py" language="python" lineStart="211" lineEnd="214"/>

2. Now that the partition has been defined we can use that in an asset that calculates the product category performance. 

```python
@dg.asset(
    deps=[joined_data],
    partitions_def=product_category_partition,
    group_name="analysis",
    compute_kind="duckdb",
)
def product_performance(context: dg.AssetExecutionContext, duckdb: DuckDBResource):
    product_category_str = context.partition_key

    with duckdb.get_connection() as conn:
        conn.execute(
            f"""
            create table if not exists product_performance (
                product_category varchar, 
                product_name varchar,
                total_dollar_amount double,
                total_units_sold double
            );

            delete from product_performance where product_category = '{product_category_str}';

            insert into product_performance
            select
                '{product_category_str}' as product_category,
                product_name,
                sum(dollar_amount) as total_dollar_amount,
                sum(quantity) as total_units_sold
            from joined_data 
            where category = '{product_category_str}'
            group by '{product_category_str}', product_name;
            """
        )
        preview_query = f"select * from product_performance where product_category = '{product_category_str}';"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM product_performance
            WHERE product_category = '{product_category_str}';
            """
        ).fetchone()
        count = row_count[0] if row_count else 0

    return dg.MaterializeResult(
        metadata={
            "row_count": dg.MetadataValue.int(count),
            "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
        }
    )
```



## 4. Materialize partitioned assets

Now that we have our partitioned assets lets add them to our definitions object. 

Your definitions object should look like this:

```python
defs = dg.Definitions(
    assets=[products,
        sales_reps,
        sales_data,
        joined_data,
        monthly_sales_performance,
        product_performance,
    ],
    asset_checks=[missing_dimension_check],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
```

To materialize these assets :
1. Navigate to the assets page.
2. Reload definitions.
3. Select the `monthly_performance` asset then Materialize selected.
4. Ensure all partitions are selected, then launch backfill. 
5. Select the `product_performance` asset then Materialize selected. 
6. Ensure all partitions are selected, then launch backfill.

## Next Steps

Now that we have the main assets in our ETL pipeline, its time to add [automation to our pipeline](automate-your-pipeline)
