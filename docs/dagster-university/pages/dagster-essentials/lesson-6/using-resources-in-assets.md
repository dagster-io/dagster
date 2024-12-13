---
title: 'Lesson 6: Using resources in assets'
module: 'dagster_essentials'
lesson: '6'
---

# Using resources in assets

Now that you’ve defined a resource, let’s refactor the `taxi_trips` asset to use it.

Let’s start by looking at the before and after.

---

## Before adding a resource

The following code shows what the `taxi_trips` asset currently looks like, without a resource:

```python
# assets/trips.py

import requests
import duckdb
import os
from . import constants
from dagster import asset

... # other assets

@asset(
    deps=["taxi_trips_file"],
)
def taxi_trips() -> None:
    query = """
        create or replace table taxi_trips as (
          select
            VendorID as vendor_id,
            PULocationID as pickup_zone_id,
            DOLocationID as dropoff_zone_id,
            RatecodeID as rate_code_id,
            payment_type as payment_type,
            tpep_dropoff_datetime as dropoff_datetime,
            tpep_pickup_datetime as pickup_datetime,
            trip_distance as trip_distance,
            passenger_count as passenger_count,
            total_amount as total_amount
          from 'data/raw/taxi_trips_2023-03.parquet'
        );
    """

    conn = backoff(
        fn=duckdb.connect,
        retry_on=(RuntimeError, duckdb.IOException),
        kwargs={
            "database": os.getenv("DUCKDB_DATABASE"),
        },
        max_retries=10,
    )
    conn.execute(query)
```

---

## After adding a resource

And now, after adding a resource, the `taxi_trips` asset looks like the following code.

```python
# assets/trips.py

import requests
from dagster_duckdb import DuckDBResource
from . import constants
from dagster import asset

... # other assets

@asset(
    deps=["taxi_trips_file"],
)
def taxi_trips(database: DuckDBResource) -> None:
    query = """
        create or replace table taxi_trips as (
          select
            VendorID as vendor_id,
            PULocationID as pickup_zone_id,
            DOLocationID as dropoff_zone_id,
            RatecodeID as rate_code_id,
            payment_type as payment_type,
            tpep_dropoff_datetime as dropoff_datetime,
            tpep_pickup_datetime as pickup_datetime,
            trip_distance as trip_distance,
            passenger_count as passenger_count,
            total_amount as total_amount
          from 'data/raw/taxi_trips_2023-03.parquet'
        );
    """

    with database.get_connection() as conn:
        conn.execute(query)
```

To refactor `taxi_trips` to use the `database` resource, we had to:

1. Replace the `duckdb` import with `from dagster_duckdb import DuckDBResource`, which we used to add type hints to the Dagster project
2. Update the `taxi_trips` asset’s function definition to include `database: DuckDBResource`. This type hint is required to tell Dagster that the dependency is a resource and not an asset.
3. Replace the lines that connect to DuckDB and execute a query:

   ```python
   conn = backoff(
       fn=duckdb.connect,
       retry_on=(RuntimeError, duckdb.IOException),
       kwargs={
           "database": os.getenv("DUCKDB_DATABASE"),
       },
       max_retries=10,
   )
   conn.execute(query)
   ```

   With these, which uses the `database` resource:

   ```python
   with database.get_connection() as conn:
       conn.execute(query)
   ```

   Notice that we no longer need to use the `backoff` function. The Dagster `DuckDBResource` handles this functionality for us.

---

## Before you continue

Before continuing, make sure you:

1. Update `asset/trips.py` with the refactored `taxi_trips` asset code
2. Reload the definitions in the Dagster UI
3. Rematerialize the `taxi_trips` asset
