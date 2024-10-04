# Changelog

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
