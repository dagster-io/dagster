---
title: 'Lesson 9: Creating an asset triggered by a sensor'
module: 'dagster_essentials'
lesson: '9'
---

# Creating an asset triggered by a sensor

Now that you’ve defined how the asset can be materialized, let’s create the ad hoc report asset.

1. Add the following imports to `requests.py`:

   ```python
   from dagster import asset, Config
   from dagster_duckdb import DuckDBResource

   import matplotlib.pyplot as plt

   from . import constants
   ```

2. Create a new asset named `adhoc_request` with the following arguments:

   1. `config`, type annotated to `AdhocRequestConfig`
   2. the `taxi_zones` and `taxi_trips` assets as dependencies
   3. `database`, type annotated to `DuckDBResource` to be able to query DuckDB.

   The asset should look like this at this point:

   ```python
   @asset(
       deps=["taxi_zones", "taxi_trips"]
   )
   def adhoc_request(config: AdhocRequestConfig, database: DuckDBResource) -> None:
   ```

3. When the report is written to a file, it should have a similar name to the request. A template has been provided in `assets/constants.py` that contains a template named `REQUEST_DESTINATION_TEMPLATE_FILE_PATH` .

   Generate the file name by using the template and stripping the `.json` extension from the request’s file name:

   ```python
   file_path = constants.REQUEST_DESTINATION_TEMPLATE_FILE_PATH.format(config.filename.split('.')[0])
   ```

4. Next, write a SQL query that:

   - Filters out trips that didn’t start in the named borough during the provided date range
   - Aggregates the data by the day of week and hour the trip started

     For example:

     ```python
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
     ```

5. Next, run the query in DuckDB and store the results as a DataFrame:

   ```python
   with database.get_connection() as conn:
       results = conn.execute(query).fetch_df()
   ```

6. Now that the query data is stored as a DataFrame in the `results` variable, use the Matplotlib library to visualize the frequency of trips at each time of the day for the borough, stratified by the day of the week:

   ```python
   fig, ax = plt.subplots(figsize=(10, 6))

   # Pivot data for stacked bar chart
   results_pivot = results.pivot(index="hour_of_day", columns="day_of_week", values="num_trips")
   results_pivot.plot(kind="bar", stacked=True, ax=ax, colormap="viridis")

   ax.set_title(f"Number of trips by hour of day in {config.borough}, from {config.start_date} to {config.end_date}")
   ax.set_xlabel("Hour of Day")
   ax.set_ylabel("Number of Trips")
   ax.legend(title="Day of Week")

   plt.xticks(rotation=45)
   plt.tight_layout()
   ```

7. Lastly, save the report to the destination file specified by the `file_path` variable you declared earlier:

   ```python
   plt.savefig(file_path)
   plt.close(fig)
   ```

Verify that `requests.py` file looks like the code below:

```python
from dagster import Config, asset
from dagster_duckdb import DuckDBResource

import matplotlib.pyplot as plt

from . import constants

class AdhocRequestConfig(Config):
    filename: str
    borough: str
    start_date: str
    end_date: str

@asset(
    deps=["taxi_zones", "taxi_trips"]
)
def adhoc_request(config: AdhocRequestConfig, database: DuckDBResource) -> None:
    """
      The response to an request made in the `requests` directory.
      See `requests/README.md` for more information.
    """

    # strip the file extension from the filename, and use it as the output filename
    file_path = constants.REQUEST_DESTINATION_TEMPLATE_FILE_PATH.format(config.filename.split('.')[0])

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
    
    ax.set_title(f"Number of trips by hour of day in {config.borough}, from {config.start_date} to {config.end_date}")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Trips")
    ax.legend(title="Day of Week")
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(file_path)
    plt.close(fig)
```
