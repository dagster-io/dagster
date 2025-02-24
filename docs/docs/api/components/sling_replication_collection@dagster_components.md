
## Component: `dagster_components.sling_replication_collection`

### Description:
Expose one or more Sling replications to Dagster as assets.

### Sample Component Params:

```yaml
type: dagster_components.sling_replication_collection

params:
  sling:
    connections:
      - name: '...'
        type: '...'
        connection_string: '...'
  replications:
    - path: '...'
      op:
        name: '...'
        tags: {}
      asset_attributes: # Available scope: {'stream_definition'}
        deps: # Available scope: {'stream_definition'}
          - '...' # Available scope: {'stream_definition'}
        description: '...' # Available scope: {'stream_definition'}
        metadata: '...' # Available scope: {'stream_definition'}
        group_name: '...' # Available scope: {'stream_definition'}
        skippable: false # Available scope: {'stream_definition'}
        code_version: '...' # Available scope: {'stream_definition'}
        owners: # Available scope: {'stream_definition'}
          - '...' # Available scope: {'stream_definition'}
        tags: '...' # Available scope: {'stream_definition'}
        kinds: # Available scope: {'stream_definition'}
          - '...' # Available scope: {'stream_definition'}
        automation_condition: '...' # Available scope: {'stream_definition'}
        key: '...' # Available scope: {'stream_definition'}
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
