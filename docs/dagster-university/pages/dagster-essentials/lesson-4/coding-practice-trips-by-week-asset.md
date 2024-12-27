---
title: 'Lesson 4: Practice: Create a trips_by_week asset'
module: 'dagster_essentials'
lesson: '4'
---

# Practice: Create a trips_by_week asset

To practice what you’ve learned, create an asset in `metrics.py` that:

- Is named `trips_by_week`
- Produces a CSV that:
  - Is saved in `constants.TRIPS_BY_WEEK_FILE_PATH`
  - Has the following schema:
    - `period` - a string representing the Sunday of the week aggregated by, ex. `2023-03-05`
    - `num_trips` - The total number of trips that started in that week
    - `passenger_count` - The total number of passengers that were on a taxi trip that week
    - `total_amount` - The total sum of the revenue produced by trips that week
    - `trip_distance` - The total miles driven in all trips that happened that week

{% callout %}

> 💡 **Extra credit!** If you want a challenge, follow this constraint:
> Imagine that the entire `trips` data is too big to fit into memory. However, a week’s worth of data fits comfortably. How would you structure your asset’s function to accommodate this?

{% /callout %}

---

## Tips

- Everything you need to know about Dagster has been covered
- There are many ways to solve these problems, such as within a database or aggregating a DataFrame
- No additional imports are needed, but you can import whatever you need
- For convenience and to accommodate for data quality issues, you can hard code the start date and end dates of the analysis to be the range of data you have (ex. `2023-03-01` to `2023-03-03`)
- DuckDB has a [`date_trunc`](https://duckdb.org/docs/sql/functions/date.html#date-functions) function that accepts `'week’` as a valid precision to truncate down to
- DuckDB also supports adding time: `+ interval '1 week'`

The numbers might not add up exactly this way, but the following is an example of what the output may look like:

```shell
period,num_trips,total_amount,trip_distance,passenger_count
2023-03-05,679681,18495110.72,2358944.42,886486
2023-03-12,686461,19151177.45,2664123.87,905296
2023-03-19,640158,17908993.09,2330611.91,838066
```

---

## Check your work

The asset you built should look similar to the following code. Click **View answer** to view it.

Note that the solution below is one of many possible ways to solve this challenge. Your way can be completely valid and more performant than this one!

We’ll assume your code looks like the following for the rest of the module. Despite not being the highest quality code, it’s flexible enough for us to extend in a later section.

**If there are differences**, compare what you wrote to the asset below, change it, and then re-materialize the asset to prepare for the next lesson.

```python {% obfuscated="true" %}
from datetime import datetime, timedelta
from . import constants

import pandas as pd
from dagster._utils.backoff import backoff

@asset(
    deps=["taxi_trips"]
)
def trips_by_week() -> None:
    conn = backoff(
        fn=duckdb.connect,
        retry_on=(RuntimeError, duckdb.IOException),
        kwargs={
            "database": os.getenv("DUCKDB_DATABASE"),
        },
        max_retries=10,
    )

    current_date = datetime.strptime("2023-03-01", constants.DATE_FORMAT)
    end_date = datetime.strptime("2023-04-01", constants.DATE_FORMAT)

    result = pd.DataFrame()

    while current_date < end_date:
        current_date_str = current_date.strftime(constants.DATE_FORMAT)
        query = f"""
            select
                vendor_id, total_amount, trip_distance, passenger_count
            from trips
            where date_trunc('week', pickup_datetime) = date_trunc('week', '{current_date_str}'::date)
        """

        data_for_week = conn.execute(query).fetch_df()

        aggregate = data_for_week.agg({
            "vendor_id": "count",
            "total_amount": "sum",
            "trip_distance": "sum",
            "passenger_count": "sum"
        }).rename({"vendor_id": "num_trips"}).to_frame().T # type: ignore

        aggregate["period"] = current_date

        result = pd.concat([result, aggregate])

        current_date += timedelta(days=7)

    # clean up the formatting of the dataframe
    result['num_trips'] = result['num_trips'].astype(int)
    result['passenger_count'] = result['passenger_count'].astype(int)
    result['total_amount'] = result['total_amount'].round(2).astype(float)
    result['trip_distance'] = result['trip_distance'].round(2).astype(float)
    result = result[["period", "num_trips", "total_amount", "trip_distance", "passenger_count"]]
    result = result.sort_values(by="period")

    result.to_csv(constants.TRIPS_BY_WEEK_FILE_PATH, index=False)
```
