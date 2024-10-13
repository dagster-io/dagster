---
title: 'Lesson 4: Assets and database execution'
module: 'dagster_essentials'
lesson: '4'
---

# Assets and database execution

At the end of the previous lesson, you created two assets that don’t depend on each other: `taxi_trips_file` during the lesson and `taxi_zones_file` during the **Practice problem** section. In this section, you’ll create additional assets that depend on these assets.

Before doing any work that requires the data files, we should load them into a database for optimal efficiency and storage. Luckily, the project template you started with comes with DuckDB installed.

DuckDB has multiple features that make it easy to ingest data into it, such as directly querying from a file. To load the `taxi_trips` file into a DuckDB database, you could run the following SQL query:

```sql
create or replace table trips as (
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
```

Don’t worry about how to run this query right now - we’ll get into that in the next section.
