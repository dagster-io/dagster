
## Component: `dagster_components.pipes_subprocess_script_collection`

### Description:
Assets that wrap Python scripts executed with Dagster's PipesSubprocessClient.

### Sample Component Params:

```yaml
type: dagster_components.pipes_subprocess_script_collection

params:
  scripts:
    - path: '...'
      assets:
        - deps:
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
