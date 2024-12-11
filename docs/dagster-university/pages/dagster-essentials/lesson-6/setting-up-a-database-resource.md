---
title: 'Lesson 6: Setting up a database resource'
module: 'dagster_essentials'
lesson: '6'
---

# Setting up a database resource

Throughout this module, you’ve used DuckDB to store and transform your data. Each time you’ve used DuckDB in an asset, you’ve needed to make a connection to it. For example:

```python
@asset(
    deps=["taxi_trips_file"],
)
def taxi_trips() -> None:
    ...
    conn = backoff(
        fn=duckdb.connect,
        retry_on=(RuntimeError, duckdb.IOException),
        kwargs={
            "database": os.getenv("DUCKDB_DATABASE"),
        },
        max_retries=10,
    )
    ...
```

Every asset that queries DuckDB contains the `duckdb.connect` line. As previously mentioned, this can become brittle and error-prone as your project grows, whether in the number of assets that use it or the complexity of the connections. For example, to MotherDuck, a specific S3 bucket, or loading an extension. To be exact, this brittleness is shared across the following assets:

- `taxi_zones`
- `taxi_trips`
- `manhattan_stats`
- `trips_by_week`

Let’s use a Dagster resource to manage this connection and share it across all the assets using it.

---

## Defining a resource

When you created the project from the template in Lesson 2, you also made a `resources` folder that contains another `__init__.py` file. In this file, you’ll define a resource that’ll be shared throughout your Dagster project.

Copy and paste the following code into `resources/__init__.py:`

```python
from dagster_duckdb import DuckDBResource

database_resource = DuckDBResource(
    database="data/staging/data.duckdb"
)
```

This code snippet imports a resource called `DuckDBResource` from Dagster’s `dagster_duckdb` integration library. Next, it creates an instance of that resource and stores it in `database_resource`.

---

## Using environment variables

When working across different settings or with secure values like passwords, environment variables are a standardized way to store configurations and credentials. Not specific to Python, environment variables are values that are saved outside of software and used within it. For a primer on environment variables in Python, check out [this post from our blog](https://dagster.io/blog/python-environment-variables).

When configuring resources, it’s best practice to load your configurations and secrets into your programs from environment variables. You’ve been following this pattern by using `os.getenv` to fetch environment variables from the `.env` file you created in Lesson 2. A `.env` file is a standard for project-level environment variables and should **not** be committed to git, as they often contain passwords and sensitive information.

However, in this project, our `.env` file only contains one environment variable: `DUCKDB_DATABASE`. This variable contains the hard-coded path to the DuckDB database file, which is `data/staging/data.duckdb`. Let’s clean up this code by using Dagster’s `EnvVar` utility.

In `resources/__init__.py`, replace the value of the `database` with an `EnvVar` as shown below:

```python
from dagster_duckdb import DuckDBResource
from dagster import EnvVar

database_resource = DuckDBResource(
    database=EnvVar("DUCKDB_DATABASE")      # replaced with environment variable
)
```

`EnvVar` is similar to the `os.getenv` method that you’ve been using, but there is a key difference:

- `EnvVar` fetches the environmental variable’s value **every time a run starts**
- `os.getenv` fetches the environment variable **when the code location is loaded**

By using `EnvVar` instead of `os.getenv`, you can dynamically customize a resource’s configuration. For example, you can change which DuckDB database is being used without having to restart Dagster’s web server.

---

## Updating the Definitions object

In the previous lesson, you learned about code locations, how they work, and how to collect assets and other Dagster definitions using the `Definitions` object.

As resources are a type of Dagster definition, you’ll need to add them to the `Definitions` object before you can use them.

Update `dagster_university/__init__.py` with the following changes:

1. Import the `database_resource` you made from the `resources` sub-module:

   ```python
   from .resources import database_resource
   ```

2. Add the imported `database_resource` to your `Definitions` object through the `resources` argument. We’ll give it the identifier `database`. This is the key that we’ll use to tell Dagster that we want the DuckDB resource.

   ```python
   defs = Definitions(
       assets=[*trip_assets, *metric_assets],
       resources={
           "database": database_resource,
       },
   )
   ```

3. In the Dagster UI, click **Deployment.**

4. In the **Code locations** tab, click the **Reload** button next to the `dagster_university` code location.

5. Click the code location to open it.

6. In the code location page that displays, click the **Resources tab.** A resource named `database` should be displayed in the tab:

   ![The Resources tab in the Dagster UI, showing the database resource for the dagster_university code location](/images/dagster-essentials/lesson-6/resources-tab.png)

   Notice that the **Uses** column is currently **0.** This is because while the resource has been defined and loaded, none of the assets in the code location are currently using it.

Now that you've set up the resource, it's time to use it in your project. In the next section, you'll learn how to refactor your assets to use resources.
