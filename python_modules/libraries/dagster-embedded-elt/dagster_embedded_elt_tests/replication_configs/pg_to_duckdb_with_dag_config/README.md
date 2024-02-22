This is some helper code for internally testing the integration with Sling.

Run `make run` to build and run a simple Postgres instance that is fed with some
sample data. 

Run the job in `sling_dag.py` with `dagster dev -f sling_dag.py` to see Dagster
load the assets from the replication file, and sync data from PG to DuckDB using
Sling.

You can interact with the duckdb instance which defaults to /var/tmp/duckdb.db

This folder is not currently used for automated testing. 