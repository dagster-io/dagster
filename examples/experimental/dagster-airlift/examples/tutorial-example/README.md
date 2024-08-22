## Example: peering airflow with Dagster

With no changes to airflow code, and minimal dagster code, `dagster-airlift` allows you to "peer" your
airflow dags into dagster as assets.

### Try it out

Run the `dev_install` make command to install python dependencies.

```bash
make dev_install
```

Launch airflow, where we've loaded the `rebuild_customers_list` DAG.

```bash
make run_airflow
```
This DAG consists of three seqeuential tasks:

1. `load_raw_customers` loads a CSV file of raw customer data into duckdb.
2. `run_dbt_model` builds a series of dbt models (from [jaffle shop](https://github.com/dbt-labs/jaffle_shop_duckdb)) combining customer, order, and payment data.
3. `export_customers` exports a CSV representation of the final customer file from duckdb to disk.

In another shell, run `dagster dev`, where you should see the full dbt-airflow lineage show up.

```bash
make run_dagster_dev
```
