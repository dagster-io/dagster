---
title: Snowflake patterns and best practices
description: Best practices and advanced patterns for Snowflake.
sidebar_position: 500
---

This guide covers advanced patterns and best practices for integrating Snowflake with Dagster.

## EL from S3 to Snowflake with TemplatedSqlComponent

You can use `TemplatedSqlComponent` together with Snowflake's native `COPY INTO` command to load data from S3 into Snowflake without any additional dependencies like dlt or Sling. A shared SQL template handles the loading logic, and each table gets its own component definition.

### Prerequisites

Before configuring the component, you'll need:

- A [Snowflake storage integration](https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration) connecting Snowflake to your S3 bucket
- An [external stage](https://docs.snowflake.com/en/user-guide/data-load-s3-create-stage) pointing at the S3 path you want to load from

The SQL template below includes the DDL to create both the stage and the target table.

### 1. Create the SQL template

Create a shared `ingest.sql` file. It uses template variables for the database, schema, table, and stage. The highlighted section is the core logic that runs each time the asset materializes:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/snowflake/component/s3_ingest/ingest.sql"
  title="my_project/defs/s3_leads/ingest.sql"
  language="sql"
/>

### 2. Configure the component

Create a `defs.yaml` that wires up the Snowflake connection and supplies values for each template variable. Define one document per table, separated by `---` — only the table name, stage name, and S3 prefix need to change between them:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/snowflake/component/s3_ingest/defs.yaml"
  title="my_project/defs/s3_leads/defs.yaml"
  language="yaml"
/>
