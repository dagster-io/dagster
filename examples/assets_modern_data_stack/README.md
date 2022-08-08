# Assets with Modern Data Stack Example

This is an example of how to use the Software-Defined Asset APIs alongside Modern Data Stack tools (specifically, Airbyte and dbt).


## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example assets_modern_data_stack
```

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

Once you've done this, you can run:

```
dagit
```

to view this example in Dagster's UI, Dagit.

If you try to kick off a run immediately, it will fail, as there is no source data to ingest/transform, nor is there an active Airbyte connection. To get everything set up properly, read on.

## Set up local Postgres

To keep things running on a single machine, we'll use a local postgres instance as both the source and the destination for our data. You can imagine the "source" database as some online transactional database, and the "destination" as a data warehouse (something like Snowflake).

To get a postgres instance with the required source and destination databases running on your machine, you can run:

```
$ docker pull postgres
$ docker run --name mds-demo -p 5432:5432 -e POSTGRES_PASSWORD=password -d postgres
$ PGPASSWORD=password psql -h localhost -p 5432 -U postgres -d postgres -c "CREATE DATABASE postgres_replica;"
```

## Set up Airbyte

Now, you'll want to get Airbyte running locally. The full instructions can be found [here](https://docs.airbyte.com/deploying-airbyte/local-deployment), but if you just want to run some commands (in a separate terminal):

```
$ git clone https://github.com/airbytehq/airbyte.git
$ cd airbyte
$ docker-compose up
```

Once you've done this, you should be able to go to http://localhost:8000, and see Airbyte's UI.

## Set up data and connections

Now, you'll want to seed some data into the empty database you just created, and create an Airbyte connection between the source and destination databases.

There's a script provided that should handle this all for you, which you can run with:

```
$ python -m assets_modern_data_stack.utils.setup_airbyte
```

At the end of this output, you should see something like:

```
Created Airbyte Connection: c90cb8a5-c516-4c1a-b243-33dfe2cfb9e8
```

This connection id is specific to your local setup, so you'll need to update `constants.py` with this
value. Once you've update your `constants.py` file, you're good to go!
