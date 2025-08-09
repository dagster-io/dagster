import dagster as dg
from dagster_duckdb import DuckDBResource

from project_dbt.defs.partitions import monthly_partition

TAXI_ZONES_FILE_PATH = "data/raw/taxi_zones.csv"
TAXI_TRIPS_TEMPLATE_FILE_PATH = "data/raw/taxi_trips_{}.parquet"


# start_taxi_zones
@dg.asset(
    group_name="ingested",
    kinds={"duckdb"},
)
def taxi_zones(context: dg.AssetExecutionContext, database: DuckDBResource):
    """The raw taxi zones dataset, loaded into a DuckDB database."""
    taxi_zones_file_path = "https://community-engineering-artifacts.s3.us-west-2.amazonaws.com/dagster-university/data/taxi_zones.csv"

    query = f"""
        create or replace table zones as (
            select
                LocationID as zone_id,
                zone,
                borough,
                the_geom as geometry
            from '{taxi_zones_file_path}'
        );
    """

    with database.get_connection() as conn:
        conn.execute(query)


# end_taxi_zones


# start_taxi_trips
@dg.asset(
    partitions_def=monthly_partition,
    group_name="ingested",
    kinds={"duckdb"},
)
def taxi_trips(context: dg.AssetExecutionContext, database: DuckDBResource):
    """The raw taxi trips dataset, loaded into a DuckDB database, partitioned by month."""
    partition_date_str = context.partition_key
    month_to_fetch = partition_date_str[:-3]
    taxi_trips_template_file_path = (
        f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month_to_fetch}.parquet"
    )

    query = f"""
        create table if not exists trips (
            vendor_id integer, pickup_zone_id integer, dropoff_zone_id integer,
            rate_code_id double, payment_type integer, dropoff_datetime timestamp,
            pickup_datetime timestamp, trip_distance double, passenger_count double,
            total_amount double, partition_date varchar
        );

        delete from trips where partition_date = '{month_to_fetch}';
    
        insert into trips
        select
            VendorID, PULocationID, DOLocationID, RatecodeID, payment_type, tpep_dropoff_datetime, 
            tpep_pickup_datetime, trip_distance, passenger_count, total_amount, '{month_to_fetch}' as partition_date
        from '{taxi_trips_template_file_path}';
    """

    with database.get_connection() as conn:
        conn.execute(query)


# end_taxi_trips
