
## Component: `dagster_components.dbt_project`

### Description:
Expose a DBT project to Dagster as a set of assets.

### Sample Component Params:

```yaml
type: dagster_components.dbt_project

params:
  dbt:
    project_dir: '...'
    global_config_flags:
      - '...'
    profiles_dir: '...'
    profile: '...'
    target: '...'
    dbt_executable: '...'
    state_path: '...'
  op:
    name: '...'
    tags: {}
  asset_attributes: # Available scope: {'node'}
    deps: # Available scope: {'node'}
      - '...' # Available scope: {'node'}
    description: '...' # Available scope: {'node'}
    metadata: '...' # Available scope: {'node'}
    group_name: '...' # Available scope: {'node'}
    skippable: false # Available scope: {'node'}
    code_version: '...' # Available scope: {'node'}
    owners: # Available scope: {'node'}
      - '...' # Available scope: {'node'}
    tags: '...' # Available scope: {'node'}
    kinds: # Available scope: {'node'}
      - '...' # Available scope: {'node'}
    automation_condition: '...' # Available scope: {'node'}
    key: '...' # Available scope: {'node'}
  transforms:
    - target: '...'
      operation: '...'
      attributes:
        deps:
          - '...'
        description: '...'
        metadata: '...'
        group_name: '...'
        skippable: false
        code_version: '...'
        owners:
          - '...'
        tags: '...'
        kinds:
          - '...'
        automation_condition: '...'
        key: '...'

```
