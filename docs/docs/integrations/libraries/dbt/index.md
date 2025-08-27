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

:::tip[dbt Fusion is supported as of 1.11.5]

Dagster supports dbt Fusion as of the 1.11.5 release. Dagster will automatically detect which engine you have installed. If you're currently using core, to migrate uninstall dbt-core and install dbt Fusion. For more information please reference the dbt [docs](https://docs.getdbt.com/docs/dbt-versions/core-upgrade/upgrading-to-fusion).

This feature is still in preview pending dbt Fusion GA.
:::

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
