## Example: peering airflow with Dagster

With no changes to airflow code, and minimal dagster code, `dagster-airlift` allows you to "peer" your
airflow dags into dagster as assets.

### Try it out

Run the `dev_install` make command to install python dependencies.

```bash
make dev_install
```

Launch airflow, where we've loaded two dags:

- `load_lakehouse`, which ingests a csv file into a duckdb table called `iris_table`
- `dbt_dag`, which loads a modified jaffle shop project, and has `iris_table` as a dbt source.

```bash
make run_airflow
```

In another shell, run `dagster dev`, where you should see the full dbt-airflow lineage show up.

```bash
make run_dagster_dev
```
