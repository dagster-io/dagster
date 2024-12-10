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

<CodeExample filePath="integrations/dbt.py" language="python" />

### About dbt

**dbt** is a SQL-first transformation workflow that lets teams quickly and collaboratively deploy analytics code following software engineering best practices like modularity, portability, CI/CD, and documentation.

<aside className="rounded-lg">

Are you looking to learn more on running Dagster with dbt? Explore the [Dagster University dbt course](https://courses.dagster.io/courses/dagster-dbt).

</aside>
