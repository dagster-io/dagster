---
title: Dagster & dbt
sidebar_label: dbt
description: Orchestrate your dbt transformations directly with Dagster.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
partnerlink: https://www.getdbt.com/
canonicalUrl: '/integrations/libraries/dbt'
slug: '/integrations/libraries/dbt'
---

<p>{frontMatter.description}</p>

Dagster assets understand dbt at the level of individual dbt models. This means that you can:

- Use Dagster's UI or APIs to run subsets of your dbt models, seeds, and snapshots.
- Track failures, logs, and run history for individual dbt models, seeds, and snapshots.
- Define dependencies between individual dbt models and other data assets. For example, put dbt models after the Fivetran-ingested table that they read from, or put a machine learning after the dbt models that it's trained from.

## Installation

<PackageInstallInstructions packageName="dagster-dbt" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt.py" language="python" />

## About dbt

**dbt** is a SQL-first transformation workflow that lets teams quickly and collaboratively deploy analytics code following software engineering best practices like modularity, portability, CI/CD, and documentation.

<aside className="rounded-lg">

:::info

Are you looking to learn more on running Dagster with dbt? Explore the [Dagster University dbt course](https://courses.dagster.io/courses/dagster-dbt).

:::

</aside>
