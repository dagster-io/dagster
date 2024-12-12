---
title: 'Lesson 8: Adding partitions to assets'
module: 'dagster_essentials'
lesson: '8'
---

# Adding partitions to assets

In this section, you’ll update the assets in `assets/trips.py` to use the partitions.

Starting with `taxi_trips_file`, the asset code should currently look like this:

```python
@asset
def taxi_trips_file() -> None:
    """
      The raw parquet files for the taxi trips dataset. Sourced from the NYC Open Data portal.
    """
    month_to_fetch = '2023-03'
    raw_trips = requests.get(
        f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month_to_fetch}.parquet"
    )

    with open(constants.TAXI_TRIPS_TEMPLATE_FILE_PATH.format(month_to_fetch), "wb") as output_file:
        output_file.write(raw_trips.content)
```

In this asset, `month_to_fetch` is set to `2023-03` to retrieve trip data for March 2023. Using the `monthly_partition`, you can update the asset to use the partition to retrieve three months of data.

To add the partition to the asset:

1. Import the `monthly_partition` from the `partitions` folder by adding the following to the top of `assets/trips.py`:

   ```python
   from ..partitions import monthly_partition
   ```

2. In the asset decorator (`@asset`), add a `partitions_def` parameter equal to `monthly_partition`:

   ```python
   @asset(
       partitions_def=monthly_partition
   )
   ```

3. In Dagster, the `context` argument provides you with metadata about the current materialization. To access it, include it as the first argument in the asset definition function. You can enable type hinting for this by importing `AssetExecutionContext` from `dagster` and adding it to the function signature. For example, the updated asset definition should look like this:

   ```python
   from dagster import asset, AssetExecutionContext


   @asset(
       partitions_def=monthly_partition
   )
   def taxi_trips_file(context: AssetExecutionContext) -> None:
   ```

   **Note**: The `context` argument isn’t specific to partitions. However, this is the first time you've used it in Dagster University. The `context` argument provides information about how Dagster is running and materializing your asset. For example, you can use it to find out which partition Dagster is materializing, which job triggered the materialization, or what metadata was attached to its previous materializations.

4. In the original asset code, the logic was hard-coded to specifically fetch data for March 2023 (`'2023-03'`). Use the `context` argument’s `partition_key` property to dynamically fetch a specific partition’s month of data:

   ```python
   @asset(
       partitions_def=monthly_partition
   )
   def taxi_trips_file(context: AssetExecutionContext) -> None:
       partition_date_str = context.partition_key
   ```

5. In the NYC OpenData source system, the taxi trip files are structured in a `YYYY-MM` format. However, `context.partition_key` supplies the materializing partition’s date as a string in the `YYYY-MM-DD` format. Slice the string to make it match the format expected by our source system and replace our existing declaration of the `month_to_fetch` variable:

   ```python
   @asset(
       partitions_def=monthly_partition
   )
   def taxi_trips_file(context: AssetExecutionContext) -> None:
       partition_date_str = context.partition_key
       month_to_fetch = partition_date_str[:-3]
   ```

After following the steps above, the `taxi_trips_file` asset should look similar to the code snippet below:

```python
from ..partitions import monthly_partition

@asset(
    partitions_def=monthly_partition
)
def taxi_trips_file(context: AssetExecutionContext) -> None:
  """
      The raw parquet files for the taxi trips dataset. Sourced from the NYC Open Data portal.
  """

  partition_date_str = context.partition_key
  month_to_fetch = partition_date_str[:-3]

  raw_trips = requests.get(
      f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month_to_fetch}.parquet"
  )

  with open(constants.TAXI_TRIPS_TEMPLATE_FILE_PATH.format(month_to_fetch), "wb") as output_file:
      output_file.write(raw_trips.content)
```
