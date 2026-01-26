---
title: Snowflake SQL component
sidebar_position: 300
description: Execute custom SQL queries in Snowflake with Dagster
tags: [dagster-supported, storage, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake
pypi: https://pypi.org/project/dagster-snowflake/
sidebar_custom_props:
  logo: images/integrations/snowflake.svg
partnerlink: https://www.snowflake.com/en/
---

Dagster provides a ready-to-use `TemplatedSQLComponent` which can be used alongside the `SnowflakeConnectionComponent` provided by the [dagster-snowflake](/integrations/libraries/snowflake/dagster-snowflake) library to execute SQL queries in Dagster to rebuild data assets in your Snowflake instance. This guide will walk you through how to use these components to execute your SQL.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source ../.venv/bin/activate" />

Finally, add the `dagster-snowflake` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/2-add-snowflake.txt" />

## 2. Scaffold a SQL component definition

Now that you have a Dagster project, you can scaffold a templated SQL component definition. You'll need to provide a name for your component instance. In this example, we'll create a component definition that will execute a SQL query to calculate the daily revenue from a table of sales transactions.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/3-scaffold-snowflake-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/4-tree.txt" />

## 3. Configure Snowflake connection

You'll need to configure a Snowflake connection component to enable the SQL component to connect to your Snowflake instance. For more information on Snowflake configuration, see the [Using Snowflake with Dagster](/integrations/libraries/snowflake/using-snowflake-with-dagster#step-1-configure-the-snowflake-resource) guide.

First, scaffold a Snowflake connection component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/6-scaffold-connection-component.txt" />

The scaffold call will generate a connection component configuration:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/7-connection-component.yaml"
  title="my_project/defs/snowflake_connection/defs.yaml"
  language="yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/8-tree.txt" />

You will only need a single connection component in your project for each Snowflake instance you'd like to connect to - this connection component can be used by multiple SQL components.

## 4. Write custom SQL

You can customize the SQL template and define the assets that will be created. Update your `defs.yaml` file with a SQL template and template variables. You can also specify properties for the asset in Dagster, such as a group name and kind tag:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/9-customized-component.yaml"
  title="my_project/defs/daily_revenue/defs.yaml"
  language="yaml"
/>

You can run `dg list defs` to see the asset corresponding to your component:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/10-list-defs.txt" />
</WideContent>

### Using an external SQL file

Instead of embedding SQL directly in your component configuration, you can store SQL in separate files. This approach provides better organization and enables SQL syntax highlighting in your editor.

First, create a SQL file with your query:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/12-sql-file.sql"
  title="my_project/defs/daily_revenue/daily_revenue.sql"
  language="sql"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/14-tree-with-sql.txt" />

Then update your component configuration to reference the external file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/13-file-based-component.yaml"
  title="my_project/defs/daily_revenue/defs.yaml"
  language="yaml"
/>

## 5. Launch your assets

Once your component is configured, you can launch your assets to execute the SQL queries:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/snowflake-sql-component/16-launch.txt" />
