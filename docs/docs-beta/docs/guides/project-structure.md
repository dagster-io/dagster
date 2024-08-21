---
title: "Structuring your Dagster project"
---

# Structuring your Dagster project

:::info
If you are looking to scaffold a new Dagster project, please refer to the project scaffolding tutorial.

:::

When it comes to organizing your project, there are many possibilities in how files and directories can be structured. Factors that can influence this includes the number of teams working on your data platform, and whether you want to structure files by Dagster concept, by technology, or by the context of the process or data.

When structuring complex projects, some important considerations are as follows:

1. The location to add new features is intuitive
2. Relevant code should be easy to find regardless of familiarity with related business logic
3. The project can be refactored and organized over time without premature optimizations

As your experience with Dagster grows, certain aspects of this guide might no longer apply to your use cases, and you may want to change the structure to adapt to your business needs.

## Default project scaffolding

By default, when you scaffold a new project using the Dagster command-line tool, an `assets.py` and `definitions.py` is created in the root of your project.

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

This is great for small projects, however, as you introduce more assets, jobs, resources, sensors, and utility code, you will want to refactor your code into multiple files.

## Restructuring growing projects

### Structured by object type

One possible structure for your project is to group your code by the type of Dagster object it implements.


This approach expands on the structure of the default project scaffolding, but as your project grows, `assets.py` file will become an `assets/` module, and your assets can be refactored into separate files. The same can be done for jobs, partitions, resources, sensors, or other concepts in Dagster.

The structure of the [fully featured project example](https://github.com/dagster-io/dagster/tree/master/examples/project_fully_featured) shown below demonstrates how files can be created for individual concepts within the modules for each Dagster concept.

```
.
├── dbt_project/
└── project_fully_featured/
    ├── assets/
    │   ├── __init__.py
    │   ├── activity_analytics/
    │   │   ├── __init__.py
    │   │   └── activity_forecast.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── id_range_for_time.py
    │   │   └── items.py
    │   └── recommender/
    │       ├── __init__.py
    │       ├── comment_stories.py
    │       ├── recommender_model.py
    │       ├── user_story_matrix.py
    │       └── user_top_recommended_stories.py
    ├── resources/
    │   ├── __init__.py
    │   ├── common_bucket_s3_pickle_io_manager.py
    │   ├── duckdb_parquet_io_manager.py
    │   ├── hn_resource.py
    │   ├── parquet_io_manager.py
    │   ├── partition_bounds.py
    │   └── snowflake_io_manager.py
    ├── sensors/
    │   ├── __init__.py
    │   ├── hn_tables_updated_sensor.py
    │   └── slack_on_failure_sensor.py
    ├── utils/
    ├── __init__.py
    ├── definitions.py
    ├── jobs.py
    └── partitions.py
```

### Structured by technology

The data engineer often has a strong understanding of the underlying technologies that are used when building pipelines. For that reason, structuring the project by the technology used can enable the engineer to easily the code base and troubleshoot issues.

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

### Structured by context

One may find it beneficial to introduce a second layer of organization encapsulating the
technologies. In this case, an ingestion and transformation module has been added around our _dlt_
and _dbt_ modules.

This provides more context to engineers who may not be as familiar with the underlying technologies
that are being used.

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

## Merging definitions

Subprojects can be encapsulated to their own `Definitions` object, and merged at the root of this project using `Definitions.merge`.

The benefit of such a structure is that dependencies like resources and partitions can be scoped to their corresponding definitions.

```py title="example-merge-definitions.py"
from dbt.definitions import dbt_definitions
from dlt.definitions import dlt_definitions


defs = Definitions.merge(
    dbt_definitions,
    dlt_definitions,
)
```

## Shared common utility

The data platform owner can enable data engineers by building frameworks and abstractions 

## Multiple code locations

So far, we've discussed our recommendations for structuring a large project which contains only one code location. Dagster also allows you to structure a project with multiple definitions.

We don't recommend over-abstracting too early; in most cases, one code location should be sufficient. A helpful pattern uses multiple code locations to separate conflicting dependencies, where each definition has its own package requirements and deployment specs.

To include multiple code locations in a single project, you'll need to add a configuration file to your project:

- **If using Dagster+**, add a dagster_cloud.yaml file to the root of your project.
- **If developing locally or deploying to your infrastructure**, add a workspace.yaml file to the root of your project.

## External projects

As your data platform evolves, Dagster will enable you to orchestrate other data tools, such as dbt, Sling, or Jupyter notebooks.

For these projects, we recommend storing them outside your Dagster project. See the `dbt_project` example below.

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
