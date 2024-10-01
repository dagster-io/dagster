---
title: "Lesson 2: dbt project files"
module: 'dagster_dbt'
lesson: '2'
---

# dbt project files

Before we get started building out the dbt project, let’s go over some of the files in the project.

---

## dbt_project.yml

From the dbt docs:

> Every [dbt project](https://docs.getdbt.com/docs/build/projects) needs a `dbt_project.yml` file — this is how dbt knows a directory is a dbt project. It also contains important information that tells dbt how to operate your project.

Refer to [the dbt documentation](https://docs.getdbt.com/reference/dbt_project.yml) for more information about `dbt_project.yml`.

---

## profiles.yml

The next file we’ll cover is the `profiles.yml` file. This file contains connection details for your data platform, such as those for the DuckDB database we’ll use in this course. In this step, we’ll set up a `dev` environment for the project to use, which is where the DuckDB database is located.

Before we start working, you should know:

- **Don’t put credentials in this file!** We’ll be pushing `profiles.yml` to git, which will compromise them. When we set up the file, we’ll show you how to use environment variables to store connection details securely.
- **We’ll create the file in the `analytics`  directory, instead of in dbt’s recommended `.dbt`.**  We’re doing this for a few reasons:
    - It allows dbt to use the same environment variables as Dagster
    - It standardizes the way connections are created as more people contribute to the project

### Set up profiles.yml

Now you’re ready - let’s go!

1. Navigate to the `analytics` directory.
2. In this folder, create a `profiles.yml` file.
3. Copy the following code into the file:
    
    ```yaml
    dagster_dbt_university:
      target: dev
      outputs:
        dev:
          type: duckdb
          path: '../{{ env_var("DUCKDB_DATABASE", "data/staging/data.duckdb") }}'
    ```
    
Let’s review what this does:

- Creates a profile named `dagster_dbt_university`
- Set the default target (data warehouse) for the `dagster_dbt_university`  profile to `dev`
- Defines one target: `dev`
- Sets the `type` to `duckdb`
- Sets the `path` using a [dbt macro](https://docs.getdbt.com/reference/dbt-jinja-functions/env_var) to reference the `DUCKDB_DATABASE` environment variable in the project’s `.env` file. With this, your dbt models will be built in the same DuckDB database as where your Dagster assets are materialized.

The `DUCKDB_DATABASE` environment variable is a relative path from the project’s root directory. For dbt to find it, we prefixed it with `../` to ensure it resolves correctly.