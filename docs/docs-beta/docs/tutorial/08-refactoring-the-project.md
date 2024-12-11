---
title: Refactoring the Project
description: Refactor the completed project into a structure that is more organized and scalable. 
last_update:
  author: Alex Noonan
---

# Refactoring code

Many engineers generally leave something alone once its working as expected. But the first time you do something is rarely the best implementation of a use case and all projects benefit from incremental improvements.

## Splitting up project structure

Right now the project is contained within one definitions file. This has gotten kinda unwieldy and if we were to add more to the project it would only get more disorganized. So we're going to create separate files for all the different Dagster core concepts: 

- Assets
- schedules
- sensors
- partitions

The final project structure should look like this:
```
dagster-etl-tutorial/
├── data/
│   └── products.csv
│   └── sales_data.csv
│   └── sales_reps.csv
│   └── sample_request/
│       └── request.json
├── etl_tutorial/
│   └── assets.py
│   └── definitions.py
│   └── partitions.py
│   └── schedules.py
│   └── sensors.py
├── pyproject.toml
├── setup.cfg
├── setup.py
```

### Assets

Assets make up a majority of our project and this will be our largest file. 

```python
from dagster_duckdb import DuckDBResource

import dagster as dg

from .partitions import monthly_partition, product_category_partition


@dg.asset(
    compute_kind="duckdb",
    group_name="ingestion",
)
def products(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            create or replace table products as (
                select * from read_csv_auto('data/products.csv')
            )
            """
        )

        preview_query = "select * from products limit 10"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute("select count(*) from products").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )
    
@dg.asset(
    compute_kind="duckdb",
    group_name="ingestion",
)
def sales_reps(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            create or replace table sales_reps as (
                select * from read_csv_auto('data/sales_reps.csv')
            )
            """
        )

        preview_query = "select * from sales_reps limit 10"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute("select count(*) from sales_reps").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )
    
@dg.asset(
    compute_kind="duckdb",
    group_name="ingestion",
)
def sales_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            drop table if exists sales_data;
            create table sales_data as select * from read_csv_auto('data/sales_data.csv')
            """
        )

        preview_query = "SELECT * FROM sales_data LIMIT 10"
        preview_df = conn.execute(preview_query).fetchdf()
        row_count = conn.execute("select count(*) from sales_data").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )

@dg.asset(
    compute_kind="duckdb",
    group_name="joins",
    deps=[sales_data, sales_reps, products],
)
def joined_data(duckdb: DuckDBResource) -> dg.MaterializeResult:
    with duckdb.get_connection() as conn:
        conn.execute(
            """
            create or replace view joined_data as (
                select 
                    date,
                    dollar_amount,
                    customer_name,
                    quantity,
                    rep_name,
                    department,
                    hire_date,
                    product_name,
                    category,
                    price
                from sales_data
                left join sales_reps
                    on sales_reps.rep_id = sales_data.rep_id
                left join products
                    on products.product_id = sales_data.product_id
            )
            """
        )

        preview_query = "select * from joined_data limit 10"
        preview_df = conn.execute(preview_query).fetchdf()

        row_count = conn.execute("select count(*) from joined_data").fetchone()
        count = row_count[0] if row_count else 0

        return dg.MaterializeResult(
            metadata={
                "row_count": dg.MetadataValue.int(count),
                "preview": dg.MetadataValue.md(preview_df.to_markdown(index=False)),
            }
        )

@dg.asset_check(asset=joined_data)
def missing_dimension_check(duckdb: DuckDBResource) -> dg.AssetCheckResult:
    with duckdb.get_connection() as conn:
        query_result = conn.execute(
            """
            select count(*) from joined_data
            where rep_name is null
            or product_name is null
            """
        ).fetchone()

        count = query_result[0] if query_result else 0
        return dg.AssetCheckResult(
            passed=count == 0, metadata={"missing dimensions": count}
        )



@dg.asset(
    partitions_def=monthly_partition,
    compute_kind="duckdb",
    group_name="analysis",
    deps=[joined_data],
    automation_condition=dg.AutomationCondition.eager(), 
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


@dg.asset(
    deps=[joined_data],
    partitions_def=product_category_partition,
    group_name="analysis",
    compute_kind="duckdb",
    automation_condition=dg.AutomationCondition.eager(), 
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


class AdhocRequestConfig(dg.Config):
    department: str
    product: str
    start_date: str
    end_date: str


@dg.asset(
    deps=["joined_data"],
    compute_kind="python",
)
def adhoc_request(
    config: AdhocRequestConfig, duckdb: DuckDBResource
) -> dg.MaterializeResult:
    query = f"""
        select
            department,
            rep_name,
            product_name,
            sum(dollar_amount) as total_sales
        from joined_data
        where date >= '{config.start_date}'
        and date < '{config.end_date}'
        and department = '{config.department}'
        and product_name = '{config.product}'
        group by
            department,
            rep_name,
            product_name
    """

    with duckdb.get_connection() as conn:
        preview_df = conn.execute(query).fetchdf()

    return dg.MaterializeResult(
        metadata={"preview": dg.MetadataValue.md(preview_df.to_markdown(index=False))}
    )

```

### Partitions

The partitions file is relatively simple and will include the `monthly_partition` and `product_category_partition`

```python 
import dagster as dg

monthly_partition = dg.MonthlyPartitionsDefinition(start_date="2024-01-01")

product_category_partition = dg.StaticPartitionsDefinition(
    ["Electronics", "Books", "Home and Garden", "Clothing"]
)
```

### Schedules

The schedules file will only contain the `weekly_update_schedule`.

```python
import dagster as dg

weekly_update_schedule = dg.ScheduleDefinition(
    name="analysis_update_job",
    target=dg.AssetSelection.keys("joined_data").upstream(),
    cron_schedule="0 0 * * 1",  # every Monday at midnight
)
```

### Sensors

The sensor file will contain the `adhoc_request_job` and the `adhoc_request_sensor`.

```python
import os
import json

import dagster as dg


adhoc_request_job = dg.define_asset_job(
    name="adhoc_request_job",
    selection=dg.AssetSelection.assets("adhoc_request"),
)

@dg.sensor(job=adhoc_request_job)
def adhoc_request_sensor(context: dg.SensorEvaluationContext):
    PATH_TO_REQUESTS = os.path.join(os.path.dirname(__file__), "../", "data/requests")

    previous_state = json.loads(context.cursor) if context.cursor else {}
    current_state = {}
    runs_to_request = []

    for filename in os.listdir(PATH_TO_REQUESTS):
        file_path = os.path.join(PATH_TO_REQUESTS, filename)
        if filename.endswith(".json") and os.path.isfile(file_path):
            last_modified = os.path.getmtime(file_path)

            current_state[filename] = last_modified

            # if the file is new or has been modified since the last run, add it to the request queue
            if (
                filename not in previous_state
                or previous_state[filename] != last_modified
            ):
                with open(file_path, "r") as f:
                    request_config = json.load(f)

                runs_to_request.append(
                    dg.RunRequest(
                        run_key=f"adhoc_request_{filename}_{last_modified}",
                        run_config={
                            "ops": {"adhoc_request": {"config": {**request_config}}}
                        },
                    )
                )

    return dg.SensorResult(
        run_requests=runs_to_request, cursor=json.dumps(current_state)
    )
```

## Adjusting definitions object

Now that we have separate files we need to adjust how the different elements are adding to definitions since they are in separate files 

1. Imports

The Dagster project runs from the root directory so whenever you are doing file references you need to have that as the starting point. 

Additionally, Dagster has functions to load all the assets `load_assets_from_modules` and asset checks `load_asset_checks_from_modules` from a module. 

2. Definitions

To bring our project together copy the following code into your `definitions.py` file:

```python
from dagster_duckdb import DuckDBResource

import dagster as dg

from .schedules import weekly_update_schedule
from .sensors import adhoc_request_sensor, adhoc_request_job
from . import assets 

tutorial_assets = dg.load_assets_from_modules([assets])
tutorial_asset_checks = dg.load_asset_checks_from_modules([assets])

defs = dg.Definitions(
    assets=tutorial_assets,
    asset_checks=tutorial_asset_checks,
    schedules=[weekly_update_schedule],
    jobs=[adhoc_request_job],
    sensors=[adhoc_request_sensor],
    resources={"duckdb": DuckDBResource(database="data/mydb.duckdb")},
)
```

## Quick Validation

If you want to validate that your definitions file loads and validates you can run the `dagster definitions validate` in the same directory that you would run `dagster dev`. This command is useful for CI/CD pipelines and allows you to check that your project loads correctly without starting the webserver. 

## Thats it!

Congratulations! You have completed your first project with Dagster and have an example of how to use the building blocks to build your own data pipelines. 

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io/) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.