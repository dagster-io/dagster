import base64

import matplotlib.pyplot as plt
from dagster import Config, MaterializeResult, MetadataValue, asset
from dagster_duckdb import DuckDBResource
from smart_open import open

from . import constants


class AdhocRequestConfig(Config):
    filename: str
    borough: str
    start_date: str
    end_date: str


@asset(
    deps=["taxi_trips", "taxi_zones"],
    compute_kind="Python",
)
def adhoc_request(config: AdhocRequestConfig, database: DuckDBResource) -> MaterializeResult:
    """The response to an request made in the `requests` directory.
    See `requests/README.md` for more information.
    """
    # strip the file extension from the filename, and use it as the output filename
    file_path = constants.REQUEST_DESTINATION_TEMPLATE_FILE_PATH.format(
        config.filename.split(".")[0]
    )

    # count the number of trips that picked up in a given borough, aggregated by time of day and hour of day
    query = f"""
        select
            date_part('hour', pickup_datetime) as hour_of_day,
            date_part('dayofweek', pickup_datetime) as day_of_week_num,
            case date_part('dayofweek', pickup_datetime)
                when 0 then 'Sunday'
                when 1 then 'Monday'
                when 2 then 'Tuesday'
                when 3 then 'Wednesday'
                when 4 then 'Thursday'
                when 5 then 'Friday'
                when 6 then 'Saturday'
            end as day_of_week,
            count(*) as num_trips
        from trips
        left join zones on trips.pickup_zone_id = zones.zone_id
        where pickup_datetime >= '{config.start_date}'
        and pickup_datetime < '{config.end_date}'
        and pickup_zone_id in (
            select zone_id
            from zones
            where borough = '{config.borough}'
        )
        group by 1, 2
        order by 1, 2 asc
    """

    with database.get_connection() as conn:
        results = conn.execute(query).fetch_df()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Pivot data for stacked bar chart
    results_pivot = results.pivot(index="hour_of_day", columns="day_of_week", values="num_trips")
    results_pivot.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")

    ax.set_title(
        f"Number of trips by hour of day in {config.borough}, from {config.start_date} to {config.end_date}"
    )
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Trips")
    ax.legend(title="Day of Week")

    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(file_path)
    plt.close(fig)

    with open(file_path, "rb") as file:
        image_data = file.read()

    # Convert the image data to base64
    base64_data = base64.b64encode(image_data).decode("utf-8")
    md_content = f"![Image](data:image/jpeg;base64,{base64_data})"

    return MaterializeResult(metadata={"preview": MetadataValue.md(md_content)})
