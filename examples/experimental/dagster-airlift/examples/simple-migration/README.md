## Example: Peering, Observing, then Migrating with Airlift

With no changes to airflow code, and minimal dagster code, `dagster-airlift` allows you to "peer" your
airflow dags into dagster as assets.

### Try it out

From the root of the `simple-migration` directory, run the `dev_install` make command to install python dependencies.

```bash
make dev_install
```

Run setup commands, which will scaffold a local airflow, dagster instance, and dbt project.

```bash
make setup_local_env
```

Launch airflow, where we've loaded one dag:

- `simple`, which has three sequential tasks: `t1` -> `t2` -> `t3`.

```bash
make run_airflow
```

In another shell, we can run dagster at the `peer`, `observe`, or `migrate` steps of the migration using any of the following commands:

```bash
make `run_peer`
make `run_observe`
make `run_migrate`
```

Note that in order to run the observation step with `run_observe`, you must set `migrated` to `False` for each task in the dags. These can be found in `./airflow_dags/migration_state/<dag_name>.yaml`.

These three steps will show the process of constructing dagster assets from each of these tasks (even when a given task actually produces multiple assets).
