---
title: 'Dagster & dbt with components'
description: The dagster-dbt library provides a DbtProjectComponent, which can be used to represent dbt models as assets in Dagster.
sidebar_position: 500
---

The [dagster-dbt](/integrations/libraries/dbt) library provides a `DbtProjectComponent`, the simplest way to represent dbt models as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source .venv/bin/activate" />

Then, add the `dagster-dbt` library to the project, along with a duckdb adapter:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/2-add-dbt.txt" />

## 2. Set up a dbt project

For this tutorial, we'll use the jaffle shop dbt project as an example. Clone it into your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/3-jaffle-clone.txt" />

We will create a `profiles.yml` file in the `dbt` directory to configure the project to use DuckDB:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/4-profiles.yml" title="dbt/profiles.yml" language="yaml" />

## 3. Scaffold a dbt component

Now that you have a Dagster project with a dbt project, you can scaffold a dbt component. You'll need to provide the path to your dbt project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/5-scaffold-dbt-component.txt" />

The scaffold call will generate a `defs.yaml` file in your project structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/6-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your dbt project:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/7-component.yaml" title="my_project/defs/dbt_ingest/defs.yaml" language="yaml" />

This is sufficient to load your dbt models as assets. You can use `dg list defs` to see the asset representation:

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/8-list-defs.txt" />
</WideContent>

## 4. Run your dbt models

To execute your dbt models, you can use the `dg launch` command to kick off a run through the CLI:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/9-dbt-run.txt" />

## 5. Select or exclude specific models

You can control which dbt models are included in your component using the `select` or `exclude` attributes. This allows you to filter which models are represented as assets, using [dbt's selection syntax](https://docs.getdbt.com/reference/node-selection/syntax). For example, to include only the `customers` model:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/10-customized-component.yaml" title="my_project/defs/dbt_ingest/defs.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/11-list-defs.txt" />
</WideContent>

## 6. Customize dbt assets

You can customize the properties of the assets emitted by each dbt model using the `translation` key in your `defs.yaml` file. This allows you to modify asset metadata such as group names, descriptions, and other properties:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/12-customized-component.yaml" title="my_project/defs/dbt_ingest/defs.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/13-list-defs.txt" />
</WideContent>
