---
title: 'Lesson 3: Defining your first asset'
module: 'dagster_essentials'
lesson: '3'
---

## Defining your first asset

In this course, you’ll use data from [NYC OpenData](https://opendata.cityofnewyork.us/) to analyze New York City taxi rides. The first asset you’ll define uses data from [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), which contains trip records for several types of vehicles. However, we’ll focus on trip data for yellow cabs in this asset.

Your first asset, which you’ll name `taxi_trips_file`, will retrieve the yellow taxi trip data for March 2023 and save it to a location on your local machine.

1. First, navigate to and open the `assets/trips.py` file in your Dagster project. This is where you’ll write your asset code.

2. At the top of the `trips.py` file, confirm the following imports already exist:

   ```python
   import requests
   from . import constants
   ```

3. Below the imports, let's define a function that takes no inputs and returns nothing (type-annoted with `None`). Add the following code to create a function to do this named `taxi_trips_file`:

   ```python
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

4. To turn the function into an asset in Dagster, you’ll need to do two things:

   1. Import `asset` from the Dagster library:

      ```python
      from dagster import asset
      ```

   2. Add the `@asset` decorator before the `taxi_trips_file` function. At this point, your code should look like this:

      ```python
      import requests
      from . import constants
      from dagster import asset

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

That’s it - you’ve created your first Dagster asset! Using the `@asset` decorator, you can easily turn any existing Python function into a Dagster asset.

**Questions about the `-> None` bit?** That's a Python feature called **type annotation**. In this case, it's saying that the function returns nothing. You can learn more about type annotations in the [Python documentation](https://docs.python.org/3/library/typing.html). We highly recommend using type annotations in your code to make it easier to read and understand.