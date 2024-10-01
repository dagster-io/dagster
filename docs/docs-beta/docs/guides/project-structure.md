---
title: "How to structure your Dagster project"
---

# How to structure your Dagster project

:::note
Refer to the project scaffolding tutorial to learn how to create a new Dagster project.
:::

There are many ways to structure your Dagster project, and it can be difficult to know where to start. In this guide, we will walk you through our recommendations for how to organize your Dagster project. As your project grows, you are welcome to deviate from these recommendations.

## Your initial project structure

When you first scaffold your project using the Dagster command-line tool, an `assets.py` and `definitions.py` are created in the root of your project.

```sh
$ dagster project scaffold --name example-dagster-project
```

```
.
├── README.md
├── example_dagster_project
│   ├── __init__.py
│   ├── assets.py
│   └── definitions.py
├── example_dagster_project_tests
│   ├── __init__.py
│   └── test_assets.py
├── pyproject.toml
├── setup.cfg
└── setup.py
```

This is a great structure as you are first getting started, however, as you begin to introduce more assets, jobs, resources, sensors, and utility code, you may find that your Python files are growing too large to manage.

## Restructure your project

There are several paradigms in which you can structure your project. Choosing one of these structures is often personal preference, and influenced by how you and your team members operate. This guide will outline three possible project structures:

1. [Option 1: Structured by technology](#option-1-structured-by-technology)
2. [Option 2: Structured by concept](#option-2-structured-by-concept)


### Option 1: Structured by technology

Data engineers often have a strong understanding of the underlying technologies that are used in their data pipelines. Because of that, it's often beneficial to organize your project by technology. This enables engineers to easily navigate the code base and locate files pertaining to the specific technology.

Within the technology modules, sub-modules can be created to further organize your code.

```
.
└── example_dagster_project/
    ├── dbt/
    │   ├── __init__.py
    │   ├── assets.py
    │   ├── resources.py
    │   └── definitions.py
    ├── dlt/
    │   ├── __init__.py
    │   ├── pipelines/
    │   │   ├── __init__.py
    │   │   ├── github.py
    │   │   └── hubspot.py
    │   ├── assets.py
    │   ├── resources.py
    │   └── definitions.py
    └── definitions.py
```

### Option 2: Structured by concept

It's also possible to introduce a layer of categorization by the overarching data processing concept. For example, whether the job is performing some kind of transformation, ingestion of data, or processing operation.

This provides additional context to the engineers who may not have as strong of a familiarity with the underlying technologies that are being used.

```
.
└── example_dagster_project/
    ├── ingestion/
    │   └── dlt/
    │       ├── assets.py
    │       ├── resources.py
    │       └── definitions.py
    ├── transformation/
    │   ├── dbt/
    │   │   ├── assets.py
    │   │   ├── resources.py
    │   │   └── partitions.py
    │   │   └── definitions.py
    │   └── adhoc/
    │       ├── assets.py
    │       ├── resources.py
    │       └── definitions.py
    └── definitions.py
```

## Merging definitions objects

It's possible to define multiple `Definitions` objects, often with one for each sub-module in your project. These definitions can then be merged at the root of your project using the `Definitions.merge` method.

The benefit of such a structure is that dependencies like resources and partitions can be scoped to their corresponding definitions.

```py title="example-merge-definitions.py"
from dbt.definitions import dbt_definitions
from dlt.definitions import dlt_definitions


defs = Definitions.merge(
    dbt_definitions,
    dlt_definitions,
)
```

## Configuring multiple code locations

This guide has outlined how to structure a project within a single code location, however, Dagster also allows you to structure a project spanning multiple location.

In most cases, one code location should be sufficient. A helpful pattern uses multiple code locations to separate conflicting dependencies, where each definition has its own package requirements and deployment specs.

To include multiple code locations in a single project, you'll need to add a configuration file to your project:

- **If using Dagster+**, add a `dagster_cloud.yaml` file to the root of your project.
- **If developing locally or deploying to your infrastructure**, add a workspace.yaml file to the root of your project.

## External projects

As your data platform evolves, Dagster will enable you to orchestrate other data tools, such as dbt, Sling, or Jupyter notebooks.

For these projects, it's recommended to store them outside your Dagster project. See the `dbt_project` example below.

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

## Next steps

- Explore the [Definitions.merge](https://docs.dagster.io/_apidocs/definitions#dagster.Definitions.merge) API docs
