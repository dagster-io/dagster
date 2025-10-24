---
description: Learn how to structure a Dagster project by technology or concept.
sidebar_position: 300
title: Organizing your Dagster project
---

:::info

To learn how to create a new Dagster project, see [Creating a new Dagster project](/guides/build/projects/creating-dagster-projects).

:::

There are many ways to structure your Dagster project, and it can be difficult to know where to start. In this guide, we will walk you through our recommendations for organizing your Dagster project.

## Your initial project structure

When you first scaffold your project using the `create-dagster` CLI, it looks like the following:

```sh
$ create-dagster project my-project
```

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    ```
    .
    └── my-project
        ├── pyproject.toml
        ├── src
        │   └── my_project
        │       ├── __init__.py
        │       ├── definitions.py
        │       └── defs
        │           └── __init__.py
        ├── tests
        │   └── __init__.py
        └── uv.lock
    ```
  </TabItem>
  <TabItem value="pip" label="pip">
    ```
    .
    └── my-project
        ├── pyproject.toml
        ├── src
        │   └── my_project
        │       ├── __init__.py
        │       ├── definitions.py
        │       └── defs
        │           └── __init__.py
        └── tests
            └── __init__.py
    ```
  </TabItem>
</Tabs>

This is a great structure as you are first getting started, however, as you begin to introduce more assets, jobs, resources, sensors, and utility code, you may find that your Python files are growing too large to manage.

## Restructure your project

There are several paradigms in which you can structure your project. Choosing one of these structures is often personal preference, and influenced by how you and your team members operate. This guide will outline three possible project structures:

1. [Option 1: Structured by technology](#option-1-structured-by-technology)
2. [Option 2: Structured by concept](#option-2-structured-by-concept)


### Option 1: Structured by technology

Data engineers often have a strong understanding of the underlying technologies that are used in their data pipelines. Because of that, it's often beneficial to organize your project by technology. This enables engineers to easily navigate the code base and locate files pertaining to the specific technology.

Within the technology modules, submodules can be created to further organize your code.

<Tabs groupId="package-manager">
<TabItem value="uv" label="uv">
        ```
        .
        ├── pyproject.toml
        ├── src
        │   └── my_project
        │       ├── __init__.py
        │       ├── definitions.py
        │       └── defs
        │           ├── __init__.py
        │           ├── dbt
        │           │   ├── assets.py
        │           │   └── resources.py
        │           └── dlt
        │               ├── assets.py
        │               ├── pipelines
        │               │   ├── github.py
        │               │   └── hubspot.py
        │               └── resources.py
        ├── tests
        │   └── __init__.py
        └── uv.lock
        ```
</TabItem>
<TabItem value="pip" label="pip">
        ```
        .
        ├── pyproject.toml
        ├── src
        │   └── my_project
        │       ├── __init__.py
        │       ├── definitions.py
        │       └── defs
        │           ├── __init__.py
        │           ├── dbt
        │           │   ├── assets.py
        │           │   └── resources.py
        │           └── dlt
        │               ├── assets.py
        │               ├── pipelines
        │               │   ├── github.py
        │               │   └── hubspot.py
        │               └── resources.py
        └── tests
            └── __init__.py
        ```
</TabItem>
</Tabs>


### Option 2: Structured by concept

You can also organize your project by data processing concept, for example, data transformation, ingestion, or processing. This provides additional context to engineers who may not be as familiar with the underlying technologies:

<Tabs groupId="package-manager">
<TabItem value="uv" label="uv">
    ```
    .
    ├── pyproject.toml
    ├── src
    │   └── my_project
    │       ├── __init__.py
    │       ├── definitions.py
    │       └── defs
    │           ├── __init__.py
    │           ├── ingestion
    │           │   └── dlt
    │           │       ├── assets.py
    │           │       └── resources.py
    │           └── transformation
    │               ├── adhoc
    │               │   ├── assets.py
    │               │   └── resources.py
    │               └── dbt
    │                   ├── assets.py
    │                   ├── partitions.py
    │                   └── resources.py
    ├── tests
    │   └── __init__.py
    └── uv.lock
    ```
</TabItem>
<TabItem value="pip" label="pip">
    ```
    .
    ├── pyproject.toml
    ├── src
    │   └── my_project
    │       ├── __init__.py
    │       ├── definitions.py
    │       └── defs
    │           ├── __init__.py
    │           ├── ingestion
    │           │   └── dlt
    │           │       ├── assets.py
    │           │       └── resources.py
    │           └── transformation
    │               ├── adhoc
    │               │   ├── assets.py
    │               │   └── resources.py
    │               └── dbt
    │                   ├── assets.py
    │                   ├── partitions.py
    │                   └── resources.py
    └── tests
        └── __init__.py
    ```
</TabItem>
</Tabs>

## Configuring multiple projects in a workspace

This guide has outlined how to structure a single project that defines a single code location. Most people will only need one project and code location. However, Dagster also allows you to create a workspace with multiple projects that define multiple code locations.

A helpful pattern uses multiple projects to separate conflicting dependencies, where each definition has its own package requirements and deployment specs.

To learn more about creating a workspace with multiple projects, see [Managing multiple projects with workspaces](/guides/build/projects/managing-multiple-projects).

## External projects

As your data platform evolves, you can integrate other data tools, such as dbt, Sling, or Jupyter notebooks.

We recommended storing these projects outside your Dagster project. See the `dbt_project` example below:

```
.
├── dbt_project/
│   ├── config/
│   │   └── profiles.yml
│   ├── dbt_project.yml
│   ├── macros/
│   │   ├── aggregate_actions.sql
│   │   └── generate_schema_name.sql
│   ├── models/
│   │   ├── activity_analytics/
│   │   │   ├── activity_daily_stats.sql
│   │   │   ├── comment_daily_stats.sql
│   │   │   └── story_daily_stats.sql
│   │   ├── schema.yml
│   │   └── sources.yml
│   └── tests/
│       └── assert_true.sql
└── example_dagster_project/
```
