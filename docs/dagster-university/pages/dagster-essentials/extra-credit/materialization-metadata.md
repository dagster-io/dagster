---
title: 'Extra credit: Materialization metadata'
module: 'dagster_essentials'
lesson: 'extra-credit'
---

# Materialization metadata

Now that we’ve covered definition metadata, let’s dive into the other type of metadata: materialization.

---

## Adding materialization metadata to an asset

To add metadata to an asset, you need to do two things:

- Return a `MaterializeResult` object with the `metadata` parameter from your asset
- Use the `MetadataValue` utility class to wrap the data, ensuring it displays correctly in the UI

Let’s add metadata to the `taxi_trips_file` asset to demonstrate further. This will add the count of records to the asset’s materialization metadata.

1. Navigate to and open `assets/trips.py`.

2. Locate the `taxi_trips_file` asset. At this point in the course, the asset should look like this:

   ```python
   from dagster import asset
   import requests
   from . import constants
   from ..partitions import monthly_partition

   @asset(
       partitions_def=monthly_partition,
       group_name="raw_files",
   )
   def taxi_trips_file(context) -> None:
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

3. First, we need to calculate the number of records contained in the file. Copy and paste the following after the last line in the asset:

   ```python
   num_rows = len(pd.read_parquet(constants.TAXI_TRIPS_TEMPLATE_FILE_PATH.format(month_to_fetch)))
   ```

4. Next, we’ll add the metadata with the specified type:

   ```python
   return MaterializeResult(
       metadata={
           'Number of records': MetadataValue.int(num_rows)
       }
   )
   ```

5. Then, since we're now returning something, let's update the return type of the asset to `MaterializeResult`:

   ```python
   from dagster import asset, MaterializeResult

   @asset(
       partitions_def=monthly_partition,
       group_name="raw_files",
   )
   def taxi_trips_file(context) -> MaterializeResult:
   ```


   Let’s break down what’s happening here:

   - Rather than returning nothing, we'll return some information about the materialization that happened with the `MaterializeResult` class.
   - The `metadata` parameter accepts a `dict`, where the key is the label or name of the metadata and the value is the data itself. In this case, the key is `Number of records`. The value in this example is everything after `Number of records`.
   - Using `MetadataValue.int`, the value of the `num_rows` variable is typed as an integer. This tells Dagster to render the data as an integer.

   At this point, the asset should look like this:

   ```python
   import pandas as pd
   from dagster import asset, MetadataValue, MaterializeResult

   @asset(
       partitions_def=monthly_partition,
       group_name="raw_files",
   )
   def taxi_trips_file(context) -> MaterializeResult:
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

       num_rows = len(pd.read_parquet(constants.TAXI_TRIPS_TEMPLATE_FILE_PATH.format(month_to_fetch)))

       return MaterializeResult(
           metadata={
               'Number of records': MetadataValue.int(num_rows)
           }
       )
   ```

---

## Materialization metadata in the Dagster UI

Next, let’s view the metadata in the Dagster UI. This is a good way to survey the data and see if everything was saved as expected.

1. Navigate to the **Global Asset Lineage** page.
2. Click **Reload definitions.**
3. When the definitions are finished loading, select the `taxi_trips_file` asset and materialization all its partitions.

After the asset has finished materializing, you’ll be able to view the plots associated with the asset:

![Rendered metadata plots for the taxi_trips_file asset in the Dagster UI](/images/dagster-essentials/extra-credit/ui-rendered-metadata-plots.png)

The X-axis of the plot is each partition, labeled with the month. The Y-axis is the number of records for that partition.

You can also view this metadata by clicking **View in Asset Catalog**, located under the name of the asset, and then the **Plots** tab.

![Rendered metadata plot for the taxi_trips_file asset in the Asset Catalog > Plots tab](/images/dagster-essentials/extra-credit/ui-plots-tab.png)
