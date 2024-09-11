---
layout: Integration
status: published
name: dbt
title: Dagster & dbt
sidebar_label: dbt
excerpt: Put your dbt transformations to work, directly from within Dagster.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-dbt
docslink: https://docs.dagster.io/integrations/dbt
partnerlink: https://www.getdbt.com/
logo: /integrations/dbt.svg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

Dagster orchestrates dbt alongside other technologies, so you can schedule dbt with Spark, Python, etc. in a single data pipeline.

Dagster assets understand dbt at the level of individual dbt models. This means that you can:

- Use Dagster's UI or APIs to run subsets of your dbt models, seeds, and snapshots.
- Track failures, logs, and run history for individual dbt models, seeds, and snapshots.
- Define dependencies between individual dbt models and other data assets. For example, put dbt models after the Fivetran-ingested table that they read from, or put a machine learning after the dbt models that it's trained from.

### Installation

```bash
pip install dagster-dbt
```

### Example

```python
from pathlib import Path

from dagster import AssetExecutionContext, Definitions
from dagster_dbt import (
    DbtCliResource,
    DbtProject,
    build_schedule_from_dbt_selection,
    dbt_assets,
)

RELATIVE_PATH_TO_MY_DBT_PROJECT = "./my_dbt_project"

my_project = DbtProject(
    project_dir=Path(__file__)
    .joinpath("..", RELATIVE_PATH_TO_MY_DBT_PROJECT)
    .resolve(),
)
my_project.prepare_if_dev()


@dbt_assets(manifest=my_project.manifest_path)
def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


my_schedule = build_schedule_from_dbt_selection(
    [my_dbt_assets],
    job_name="materialize_dbt_models",
    cron_schedule="0 0 * * *",
    dbt_select="fqn:*",
)

defs = Definitions(
    assets=[my_dbt_assets],
    schedules=[my_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=my_project),
    },
)
```

### About dbt

**dbt** is a SQL-first transformation workflow that lets teams quickly and collaboratively deploy analytics code following software engineering best practices like modularity, portability, CI/CD, and documentation.

<aside className="rounded-lg">

Are you looking to learn more on running Dagster with dbt? Explore the <a href="https://courses.dagster.io/courses/dagster-dbt">Dagster University dbt course</a>.

</aside>
