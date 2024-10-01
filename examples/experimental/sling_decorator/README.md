# (Experimental) Sling with Asset Decorators

This is an example of how to use the new Sling `@sling_assets` decorator
to sync data from Postgres to DuckDB.

In order to run this example, we will setup a Docker instance of Postgres
which some sample data to sync into DuckDB. The following steps will help you
validate that you are able to run the example locally outside of Dagster using
the included replication.yaml

## Initial Setup

First, we need to start the Postgres instance. The Makefile offers aliases
to simplify building and running a Postgres instance:

```bash
make build  # builds the docker image
make run    # runs the docker image
```

Next, validate that everything works locally:

```bash
pip install --upgrade sling
make sync   # runs sling
make verify
```

You should see output similar to this

```
                POSTGRES
--------------------------------
 all_user_id |      name
-------------+----------------
           1 | Alice Johnson
           2 | Bob Williams
           3 | Charlie Miller
(3 rows)

                DUCKDB
--------------------------------
┌─────────────┬────────────────┬──────────────────┐
│ all_user_id │      name      │ _sling_loaded_at │
│    int32    │    varchar     │      int32       │
├─────────────┼────────────────┼──────────────────┤
│           1 │ Alice Johnson  │       1708665267 │
│           2 │ Bob Williams   │       1708665267 │
│           3 │ Charlie Miller │       1708665267 │
└─────────────┴────────────────┴──────────────────┘
```

## Getting started

To download this example, run:

```shell
dagster project from-example --name my-dagster-project --example sling_decorator
```

To install this example and its dependencies, run:

```shell
cd my-dagster-project
pip install -e .
```

Now run Dagster to load the sample Sling pipeline:

```shell
dagster dev
```
