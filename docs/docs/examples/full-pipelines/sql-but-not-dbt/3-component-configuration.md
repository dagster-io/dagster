---
title: Component configuration with YAML
description: Configure data pipelines declaratively using YAML files
sidebar_position: 30
---

One of the key benefits of Dagster's component system is the ability to configure your data pipeline declaratively using YAML files. This approach separates configuration from code, making pipelines easier to maintain and modify without changing Python code.

## Component discovery and loading

Dagster automatically discovers components in your project through the `build_component_defs` function:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/definitions.py"
  language="python"
  startAfter="start_build_component_defs"
  endBefore="end_build_component_defs"
  title="src/sql_but_not_dbt/definitions.py"
/>

This single line of code:

- **Scans the `defs/` directory**: Looks for `component.yaml` files in subdirectories
- **Loads components**: Instantiates each component based on its YAML configuration
- **Creates definitions**: Builds a `Definitions` object containing all discovered assets and resources

The directory structure determines how components are organized:

```
src/sql_but_not_dbt/defs/
├── ingest_files/           # Data ingestion component
│   ├── component.yaml      # Component configuration
│   └── replication.yaml    # Sling replication config
└── sql/                    # SQL transformation component
    ├── component.yaml      # Component configuration
    └── first_5_orders.sql  # SQL query file
```

## SQL component configuration

The SQL transformation component is configured entirely through YAML:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/defs/sql/component.yaml"
  language="yaml"
  startAfter="start_sql_component_config"
  endBefore="end_sql_component_config"
  title="src/sql_but_not_dbt/defs/sql/component.yaml"
/>

Key configuration elements:

- **Type reference**: Points to the custom `SqlComponent` class we implemented
- **SQL path**: Relative path to the SQL file containing the query
- **Database URL**: DuckDB connection string pointing to the database file
- **Asset specifications**: Defines the output asset with its key, dependencies, and metadata

## Asset specification details

The `asset_specs` section defines how the component's output should be represented as a Dagster asset:

- **Key**: `first_5_orders` becomes the asset name in the Dagster UI
- **Dependencies**: `deps: [raw_orders]` creates lineage from the ingested data
- **Kinds**: Metadata tags indicating this asset uses DuckDB and SQL
- **Group name**: Commented out but could be used to organize related assets

## Configuration benefits

This YAML-based approach provides several advantages:

### Separation of concerns

Configuration is separated from implementation logic, making both easier to understand and maintain.

### Non-technical accessibility

Data analysts can modify SQL queries and asset configurations without touching Python code.

### Version control

YAML files are easily tracked in version control, providing clear audit trails for configuration changes.

### Environment-specific configuration

Different YAML files can be used for development, staging, and production environments.

## Advanced configuration patterns

The component system supports more sophisticated configuration patterns:

### Multiple asset specifications

A single component can create multiple assets:

```yaml
asset_specs:
  - key: first_5_orders
    deps: [raw_orders]
    kinds: [duckdb, sql]
  - key: recent_orders
    deps: [raw_orders]
    kinds: [duckdb, sql]
```

### Environment variables

Configuration can reference environment variables:

```yaml
sql_engine_url: 'duckdb://{{ env.DUCKDB_PATH }}/database.duckdb'
```

### Conditional configuration

Different configurations can be used based on conditions:

```yaml
sql_engine_url: >
  {% if env.ENVIRONMENT == "prod" %}
  postgresql://prod-db/analytics
  {% else %}
  duckdb:///tmp/dev.duckdb
  {% endif %}
```

## Component type registration

The `type` field in the YAML configuration references the component class:

```yaml
type: iwritesqlbutnotdbt.lib.SqlComponent
```

This string tells Dagster:

- **Module path**: `iwritesqlbutnotdbt.lib` points to the Python module
- **Class name**: `SqlComponent` is the specific component class to instantiate

Dagster uses Python's import system to dynamically load and instantiate the component class with the provided configuration.

## Configuration validation

Dagster automatically validates YAML configuration against the component's schema. The `SqlComponentModel` class defines:

- Required fields that must be present
- Field types and validation rules
- Default values for optional fields

If the YAML configuration doesn't match the expected schema, Dagster will provide clear error messages indicating what needs to be fixed.

## Best practices

When working with component configuration:

- **Keep SQL files small**: Focus on single transformations per component
- **Use descriptive asset keys**: Names should clearly indicate what the asset contains
- **Specify dependencies explicitly**: Always declare upstream assets in `deps`
- **Add appropriate kinds**: Use kinds to categorize and filter assets
- **Document complex logic**: Add comments to YAML files explaining business logic

This declarative approach makes data pipelines more maintainable and accessible to a broader range of team members, from data engineers to business analysts.

## Next steps

You now understand how to build data pipelines using:

- Sling components for data ingestion
- Custom SQL components for transformations
- YAML configuration for declarative pipeline definitions

Try extending this example by:

- Adding more SQL transformations
- Creating components for different databases
- Building custom components for your specific use cases
