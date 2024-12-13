---
title: 'Lesson 4: Loading data into a database'
module: 'dagster_essentials'
lesson: '4'
---

# Loading data into a database

Now that you have a query that produces an asset, let’s use Dagster to manage the materialization. By having Dagster manage the definition and materialization of data assets, you can easily determine when the table is changed and how long it takes.

1. At the top of the `trips.py` file, import `duckdb` and `os` to help you manage where the DuckDB database file is stored:

   ```python
   import duckdb
   import os
   from dagster._utils.backoff import backoff
   ```

2. Copy and paste the code below into the bottom of the `trips.py` file. Note how this code looks similar to the asset definition code for the `taxi_trips_file` and the `taxi_zones` assets:

   ```python
   @asset(
       deps=["taxi_trips_file"]
   )
   def taxi_trips() -> None:
       """
         The raw taxi trips dataset, loaded into a DuckDB database
       """
       query = """
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

   Let’s walk through what this code does:

   1. Using the `@asset` decorator, an asset named `taxi_trips` is created.

   2. The `taxi_trips_file` asset is defined as a dependency of `taxi_trips` through the `deps` argument.

   3. Next, a variable named `query` is created. This variable contains a SQL query that creates a table named `trips`, which sources its data from the `data/raw/taxi_trips_2023-03.parquet` file. This is the file created by the `taxi_trips_file` asset.

   4. A variable named `conn` is created, which defines the connection to the DuckDB database in the project. To do this, we first wrap everything with the Dagster utility function `backoff`. Using the backoff function ensures that multiple assets can use DuckDB safely without locking resources. The backoff function takes in the function we want to call (in this case the `.connect` method from the `duckdb` library), any errors to retry on (`RuntimeError` and `duckdb.IOException`), the max number of retries, and finally, the arguments to supply to the `.connect` DuckDB method. Here we are passing in the `DUCKDB_DATABASE` environment variable to tell DuckDB where the database is located.

      The `DUCKDB_DATABASE` environment variable, sourced from your project’s `.env` file, resolves to `data/staging/data.duckdb`. **Note**: We set up this file in Lesson 2 - refer to this lesson if you need a refresher. If this file isn’t set up correctly, the materialization will result in an error.

   5. Finally, `conn` is paired with the DuckDB `execute` method, where our SQL query (`query`) is passed in as an argument. This tells the asset that, when materializing, to connect to the DuckDB database and execute the query in `query`.

3. Save the changes to the file.

4. In the Dagster UI, navigate to the **Global asset lineage** page:

   ![The asset graph in the Dagster UI with the taxi_trips_file and taxi_zones_file assets](/images/dagster-essentials/lesson-4/asset-graph.png)

   It looks like there’s an issue - the new `taxi_trips` asset isn’t showing up. This is because the definitions in your **code location** have to be reloaded to reflect this newly added asset.

   We’ll go into code locations in detail in a later lesson, but for now, you can manually reload your definitions by clicking the **Reload Definitions** button near the top-right corner of the page.

Once reloaded, the `taxi_trips` asset will display in the asset graph:

![The taxi_trips asset, now visible in the asset graph of the Dagster UI](/images/dagster-essentials/lesson-4/taxi-trips-in-asset-graph.png)

Notice the arrow from the `taxi_trips` file asset to the `taxi_trips` asset: this indicates the dependency that `taxi_trips` has on `taxi_trips_file`.

{% callout %}

> 💡 **When should definitions be reloaded**? If you installed dependencies with `pip install -e ".[dev]"`, you’ll only need to reload definitions when adding new assets or other Dagster objects, such as schedules, to your project. Because of the `-e` editable flag, Dagster can pick up the changes in your asset function’s code without needing to reload the code location again.
> {% /callout %}

---

## Materializing the pipeline

Click the **Materialize all** button in the top right corner of the graph to create a new run that materializes all the assets. When the run starts, click the run link on the asset to open the **Run details** page. This allows you to view the run in progress.

On this page, you’ll see that all three of your assets in the process of materializing. The `taxi_trips_file` and `taxi_zones_file` assets should materialize in parallel, while `taxi_trips` won’t begin materializing until after `taxi_trips_file` finishes:

![Timeline view of taxi_trips_file, taxi_zones_file, and taxi_trips asset materialization. taxi_trips_file and taxi_zones_file materialized in parallel, while taxi_trips, waited until its parent (taxi_trips_file) finished materializing successfully.](/images/dagster-essentials/lesson-4/materialization-graph.png)

This is because you’ve told Dagster that taxi_trips depends on the taxi_trips_file asset, using the deps= argument. Therefore, the taxi_trips asset waits until the taxi_trips_file is up-to-date and materialized before trying to materialize itself.

### Optional: Verifying the materialization

To confirm that the `taxi_trips` asset materialized properly, you can access the newly made `trips` table in DuckDB. In a new terminal session, open a Python REPL and run the following snippet:

```python
import duckdb
conn = duckdb.connect(database="data/staging/data.duckdb") # assumes you're writing to the same destination as specified in .env.example
conn.execute("select count(*) from trips").fetchall()
```

The command should succeed and return a row count of the taxi trips that were ingested. When finished, make sure to stop the terminal process before continuing or you may encounter an error. Use `Control+C` or `Command+C` to stop the process.

Congratulations! You’ve finished writing a simple data pipeline that fetches data from an API and ingests it into a database.
