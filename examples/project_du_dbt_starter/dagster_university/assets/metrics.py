import base64

import dagster as dg
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from dagster_duckdb import DuckDBResource
from smart_open import open

from ..partitions import weekly_partition
from . import constants


@dg.asset(
    deps=[dg.AssetKey(["taxi_trips"])],
    partitions_def=weekly_partition,
    compute_kind="DuckDB",
)
def trips_by_week(context: dg.AssetExecutionContext, database: DuckDBResource):
    """The number of trips per week, aggregated by week.
    These date-based aggregations are done in-memory, which is expensive, but enables you to do time-based aggregations consistently across data warehouses (ex. DuckDB and BigQuery).
    """
    period_to_fetch = context.partition_key

    # get all trips for the week
    query = f"""
        select vendor_id, total_amount, trip_distance, passenger_count
        from trips
        where pickup_datetime >= '{period_to_fetch}'
            and pickup_datetime < '{period_to_fetch}'::date + interval '1 week'
    """

    with database.get_connection() as conn:
        data_for_month = conn.execute(query).fetch_df()

    aggregate = (
        data_for_month.agg(
            {
                "vendor_id": "count",
                "total_amount": "sum",
                "trip_distance": "sum",
                "passenger_count": "sum",
            }
        )
        .rename({"vendor_id": "num_trips"})
        .to_frame()
        .T
    )  # type: ignore

    # clean up the formatting of the dataframe
    aggregate["period"] = period_to_fetch
    aggregate["num_trips"] = aggregate["num_trips"].astype(int)
    aggregate["passenger_count"] = aggregate["passenger_count"].astype(int)
    aggregate["total_amount"] = aggregate["total_amount"].round(2).astype(float)
    aggregate["trip_distance"] = aggregate["trip_distance"].round(2).astype(float)
    aggregate = aggregate[
        ["period", "num_trips", "total_amount", "trip_distance", "passenger_count"]
    ]

    try:
        # If the file already exists, append to it, but replace the existing month's data
        existing = pd.read_csv(constants.TRIPS_BY_WEEK_FILE_PATH)
        existing = existing[existing["period"] != period_to_fetch]
        existing = pd.concat([existing, aggregate]).sort_values(by="period")
        existing.to_csv(constants.TRIPS_BY_WEEK_FILE_PATH, index=False)
    except FileNotFoundError:
        aggregate.to_csv(constants.TRIPS_BY_WEEK_FILE_PATH, index=False)


@dg.asset(
    deps=[dg.AssetKey(["taxi_trips"]), dg.AssetKey(["taxi_zones"])],
    key_prefix="manhattan",
    compute_kind="DuckDB",
)
def manhattan_stats(database: DuckDBResource):
    """Metrics on taxi trips in Manhattan."""
    query = """
        select
            zones.zone,
            zones.borough,
            zones.geometry,
            count(1) as num_trips,
        from trips
        left join zones on trips.pickup_zone_id = zones.zone_id
        where geometry is not null
        group by zone, borough, geometry
    """

    with database.get_connection() as conn:
        trips_by_zone = conn.execute(query).fetch_df()

    trips_by_zone["geometry"] = gpd.GeoSeries.from_wkt(trips_by_zone["geometry"])
    trips_by_zone = gpd.GeoDataFrame(trips_by_zone)

    with open(constants.MANHATTAN_STATS_FILE_PATH, "w") as output_file:
        output_file.write(trips_by_zone.to_json())


@dg.asset(
    deps=[dg.AssetKey(["manhattan", "manhattan_stats"])],
    compute_kind="Python",
)
def manhattan_map() -> dg.MaterializeResult:
    """A map of the number of trips per taxi zone in Manhattan."""
    trips_by_zone = gpd.read_file("data/staging/manhattan_stats.geojson")

    fig, ax = plt.subplots(figsize=(10, 10))
    trips_by_zone.plot(column="num_trips", cmap="plasma", legend=True, ax=ax, edgecolor="black")
    ax.set_title("Number of Trips per Taxi Zone in Manhattan")

    ax.set_xlim([-74.05, -73.90])  # Adjust longitude range
    ax.set_ylim([40.70, 40.82])  # Adjust latitude range

    # Save the image
    plt.savefig(constants.MANHATTAN_MAP_FILE_PATH, format="png", bbox_inches="tight")
    plt.close(fig)

    with open(constants.MANHATTAN_MAP_FILE_PATH, "rb") as file:
        image_data = file.read()

    # Convert the image data to base64
    base64_data = base64.b64encode(image_data).decode("utf-8")
    md_content = f"![Image](data:image/jpeg;base64,{base64_data})"

    return dg.MaterializeResult(metadata={"preview": dg.MetadataValue.md(md_content)})
