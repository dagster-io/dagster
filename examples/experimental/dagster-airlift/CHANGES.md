# Changelog

## 0.0.27

### New

- Airlift CLI: You can now proxy airlift state in your airflow directory by calling `dagster-airlift proxy scaffold` from within your Airflow codebase (airflow must be installed, and `AIRFLOW_HOME` must be set)
- `dagster-airlift[in-airflow]` no longer has a direct pin on airflow itself. Instead we rely on users installing their own 2.0.0 or greater version of Airflow.
- Dag-level mapping has been introduced. Using the `assets_with_dag_mappings` API, you can map individual assets to an entire DAG, and those assets will receive materializations on successful runs of that DAG. See the tutorial section on dag-level mapping for more.
- Python 3.12 is now explicitly supported.
- Time-windowed partitioned assets mapped to Airflow will now automatically receive partitioned materializations corresponding to the `execution_date` in airflow. See the tutorial section on partitioning for more.

### Tutorial

- Tutorial section on dealing with changing airflow
- Tutorial section on partitioning
- Tutorial section on dag-level mapping
- The tutorial has been changed to use `assets_with_task_mappings` instead of `task_defs` to maintain a consistent API across integrations.

### Breaking Changes

- Proxy operators now makes the assumption that all assets mapped to a given airflow task must be launchable within a single run (this works out of the box on Dagster 1.8 or greater).
- The `dagster_operator_klass` method has been removed, and the base class has changed. Instead of overriding `BaseProxyToDagsterOperator`, users will now subclass `BaseProxyTaskToDagsterOperator`, and use the `build_from_task_fn` argument:

```python
proxying_to_dagster(
  ...,
  # This method is implemented by default, but can be overridden.
  build_from_task_fn=MyCustomOperator.build_from_task,
)
```

## 0.0.26

### New

- Add python 3.8 support
- `BaseMaterializeAssetsOperator` for kicking off execution of a discrete set of Dagster assets from Airflow.

## 0.0.25

### Breaking Changes

- `dagster-airlift[core,mwaa,dbt]` is now pinned on Dagster >= 1.8.10.

## 0.0.24

### New

- Rebuilt `build_defs_from_airflow_instance` on top of lazy-loading Definitions abstractions.
- The initial run of `build_defs_from_airflow_instance` has been made much faster by batching retrieval of task info per dag.
- A new `targeted_by_multiple_tasks` function in `dagster_airlift.core` which allows for targeting the same set of assets from tasks in multiple dags. See the docstring for more.

### Breaking Changes

- `dagster-airlift[core,mwaa,dbt]` is now pinned on Dagster >= 1.8.8.
- `migrating` terminology has been updated to `proxied` terminology.
  - `mark_as_dagster_migrating` has been renamed to `proxying_to_dagster`
  - In examples, the `migration_state` directories have been renamed to `proxied_state`.
  - In each `yaml` file in the proxied directory, the `migrated` bit has been renamed to the `proxied` bit. So, if prior your migration file looked like this:

```yaml
# migration_state/my_dag.yaml
tasks:
  id: foo
  migrated: False
```

    it should instead look like this:

```yaml
# proxied_state/my_dag.yaml
tasks:
  id: foo
  proxied: False
```
