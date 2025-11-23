---
title: Custom SQL components
description: Build reusable SQL components for data transformations
sidebar_position: 20
---

While dbt is excellent for SQL-based transformations, sometimes you want the simplicity of writing SQL directly without learning dbt's concepts. This tutorial shows how to create a custom Dagster component that executes SQL files and integrates seamlessly with your data pipeline.

## The SQL Component architecture

The `SqlComponent` demonstrates how to build custom Dagster components that can execute arbitrary SQL queries against a database. This approach gives you the flexibility of raw SQL while maintaining Dagster's asset lineage and orchestration benefits.

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/lib/sql_component.py"
  language="python"
  startAfter="start_sql_component_model"
  endBefore="end_sql_component_model"
  title="src/sql_but_not_dbt/lib/sql_component.py"
/>

The `SqlComponentModel` defines the configuration schema for our component:

- **sql_path**: The path to the SQL file containing the query to execute
- **sql_engine_url**: The database connection URL (supports any SQLAlchemy-compatible database)
- **asset_specs**: Asset specifications that define the output assets, dependencies, and metadata

## Component implementation

The core component logic extends Dagster's `Component` base class and implements the `build_defs` method:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/lib/sql_component.py"
  language="python"
  startAfter="start_sql_component_class"
  endBefore="end_sql_component_class"
  title="src/sql_but_not_dbt/lib/sql_component.py"
/>

Key aspects of the implementation:

- **Multi-asset creation**: Uses `@dg.multi_asset` to create assets based on the configured specifications
- **Path resolution**: Resolves the SQL file path relative to the component's location
- **Asset naming**: Names the asset using the SQL file's stem (filename without extension)

## SQL execution logic

The `execute` method handles the actual SQL query execution and result processing:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/lib/sql_component.py"
  language="python"
  startAfter="start_execute_method"
  endBefore="end_execute_method"
  title="src/sql_but_not_dbt/lib/sql_component.py"
/>

The execution process:

1. **File reading**: Reads the SQL query from the specified file
2. **Database connection**: Creates a SQLAlchemy engine using the provided connection URL
3. **Query execution**: Executes the SQL query and loads results into a pandas DataFrame
4. **Result processing**: Prints the DataFrame for debugging and returns materialization metadata
5. **Metadata attachment**: Includes both the executed query and a preview of the results as metadata

## SQL query example

Here's the SQL file that the component executes in our example:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/defs/sql/first_5_orders.sql"
  language="sql"
  title="src/sql_but_not_dbt/defs/sql/first_5_orders.sql"
/>

This simple query demonstrates:

- **Table access**: Queries the `raw_orders` table created by our ingestion component
- **Data ordering**: Sorts by `order_date` to get chronologically ordered results
- **Result limiting**: Uses `LIMIT 5` to return only the first 5 orders

## Benefits of this approach

The custom SQL component provides several advantages:

- **Simplicity**: Write SQL directly without learning dbt's templating or modeling concepts
- **Flexibility**: Execute any SQL query that your database supports
- **Integration**: Seamlessly integrates with Dagster's asset system and UI
- **Metadata**: Automatically captures query text and results as asset metadata
- **Reusability**: One component definition can be reused for multiple SQL transformations

## Asset lineage and dependencies

The component automatically establishes proper asset lineage through the `deps` specification in the YAML configuration. When you specify that `first_5_orders` depends on `raw_orders`, Dagster:

- Creates the dependency relationship in the asset graph
- Ensures `raw_orders` is materialized before `first_5_orders`
- Shows the lineage visually in the Dagster UI
- Enables impact analysis when upstream data changes

## Extensibility

This basic SQL component could be extended in many ways:

- **Parameter substitution**: Add support for parameterized queries
- **Multiple outputs**: Return multiple DataFrames for queries with multiple result sets
- **Custom metadata**: Extract more sophisticated metadata from query results
- **Error handling**: Add robust error handling and retry logic
- **Connection pooling**: Implement connection pooling for better performance

The component pattern makes it easy to build reusable, configurable building blocks for your data pipelines without the complexity of a full transformation framework.

## Next steps

Now let's see how to [configure components with YAML](/examples/full-pipelines/sql-but-not-dbt/component-configuration) to create declarative pipeline definitions.
