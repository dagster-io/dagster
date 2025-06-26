---
title: 'Dagster & Snowflake with components'
description: The dagster-snowflake library provides a SnowflakeTemplatedSqlComponent, which can be used to represent templated SQL queries as assets in Dagster.
sidebar_position: 402
---

The [dagster-snowflake](/integrations/libraries/snowflake) library provides both a `BaseSnowflakeSqlComponent`, which can be used to write your own Snowflake components, and a ready-to-use `SnowflakeTemplatedSqlComponent` which can be used to execute SQL queries from Dagster in order to rebuild data assets in Snowflake. This guide will walk you through how to use the `SnowflakeTemplatedSqlComponent` to create a component that will execute custom SQL.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source ../.venv/bin/activate" />

Finally, add the `dagster-snowflake` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/2-add-snowflake.txt" />

## 2. Scaffold a Snowflake SQL component

Now that you have a Dagster project, you can scaffold a Snowflake SQL component. You'll need to provide a name for your component. In this example, we'll create a component that will execute a SQL query to calculate the daily revenue from a table of sales transactions.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/3-scaffold-snowflake-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/4-tree.txt" />

## 3. Configure Snowflake resource

You'll need to configure a Snowflake [resource](/guides/build/external-resources) to enable your component to connect to your Snowflake instance. For more information on the Snowflake resource, see the [Using Snowflake with Dagster](/integrations/libraries/snowflake/using-snowflake-with-dagster#step-1-configure-the-snowflake-resource) guide.

Create a `resources.py` file in your `defs` directory:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/6-resources.py" title="my_project/defs/resources.py" language="python" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/7-tree.txt" />

You will only need a single resource in your project for each Snowflake instance you'd like to connect to - this resource can be used by multiple components.

## 4. Write custom SQL

You can customize the SQL template and define the assets that will be created. Update your `defs.yaml` file with a SQL template and template variables. You can also specify properties for the asset in Dagster, such as a group name and kind tag:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/8-customized-component.yaml" title="my_project/defs/daily_revenue/defs.yaml" language="yaml" />

You can run `dg list defs` to see the asset corresponding to your component:

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/9-list-defs.txt" />
</WideContent>

### Using an external SQL file

Instead of embedding SQL directly in your component configuration, you can store SQL in separate files. This approach provides better organization and enables SQL syntax highlighting in your editor.

First, create a SQL file with your query:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/9-sql-file.sql" title="my_project/defs/daily_revenue/daily_revenue.sql" language="sql" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/11-tree-with-sql.txt" />

Then update your component configuration to reference the external file:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/10-file-based-component.yaml" title="my_project/defs/daily_revenue/defs.yaml" language="yaml" />

## 5. Launch your assets

Once your component is configured, you can launch your assets to execute the SQL queries:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/13-launch.txt" />
