---
title: "Jupyter/Papermill & Dagster | Dagster Docs"
description: The Dagstermill package lets you run notebooks using the Dagster tools and integrate them into your data pipelines.
---

# Dagstermill: Jupyter/Papermill & Dagster

Notebooks are an indispensible tool for data science. They allow for easy exploration of datasets, fast iteration, and the ability to create a rich report with Markdown blocks and inline plotting. The Dagstermill (Dagster & Papermill) package makes it straightforward to run notebooks using Dagster tools and to integrate them with your Dagster assets or jobs.

Using the Dagstermill library enables you to:

- View notebooks directly in the Dagster UI without needing to set up a Jupyter kernel
- Define data dependencies to flow inputs and outputs from assets/ops to notebooks, between notebooks, and from notebooks to other assets/ops
- Use Dagster resources and the Dagster config system inside notebooks
- Aggregate notebook logs with logs from other Dagster assets and ops
- Yield custom materializations and other Dagster events from your notebook code

<!-- Our goal is to make it unnecessary to go through a tedious "productionization" process where code developed in notebooks must be translated into some other (less readable and interpretable) format in order to be integrated into production workflows. Instead, we can use notebooks as assets or ops directly, with minimal changes to notebook code that still allow for standalone execution of the notebook. -->

---

## Using notebooks with Dagster

Developing in notebooks is an important part of many data science workflows. However, notebooks are often considered standalone artifacts during development: The notebook is responsible for fetching any data it needs, running the analysis, and presenting results.

This presents a number of problems, the main two being:

- **Data is siloed in the notebook.** If another developer wants to write a notebook to do additional analysis of the same dataset, they have to replicate the data loading logic in their notebook. This means that each developer must remember to update the data loading logic in each notebook whenever that logic needs to change. If the two versions of fetching data begin to drift (ie. the logic is changed in one notebook but not the other) you may get misleading conclusions.

- **Running notebooks on a schedule may miss important data.** If your notebook fetches data each day, running the notebook on a schedule could mean that the notebook runs before the new data is available. This increases the uncertainty that the conclusions produced by the notebook are based on the correct data, and could force you to manually re-run the notebook.

Integrating your notebooks into a broader Dagster project allows you to:

- **Separate data-fetching logic from analysis.** Factoring data retrieval into separate assets allows any notebook to individually retrieve data required for analysis. This creates a common source of truth for your data.

  If you need to change how an asset is created, modifying only one piece of code is required. This allows for increased discoverability of notebooks by easily seeing which notebooks analyze a particular dataset.

- **Execute notebooks in response when new data is detected.** Using [sensors](/concepts/partitions-schedules-sensors/sensors), Dagster can execute notebooks in response to new data being made available. Not only does this simplify scheduling, it also ensures that notebooks are using the most up-to-date data and prevents redundant executions if the data doesn't change.

---

## Jupyter, Papermill, and Dagster tutorial

In this tutorial, we'll walk you through integrating Jupyter notebooks with Dagster using an example Jupyter notebook and the `dagstermill` library. [Click here to get started](/integrations/dagstermill/using-notebooks-with-dagster).

By the end of the tutorial, you'll have a working integration with Jupyter and Papermill integration and a handful of materialized Dagster assets.

---

## References

<ArticleList>
  <ArticleListItem
    title="Dagstermill integration reference"
    href="/integrations/dagstermill/reference"
  ></ArticleListItem>
  <ArticleListItem
    title="dagstermill API reference"
    href="/api/python-api/libraries/dagstermill"
  ></ArticleListItem>
</ArticleList>
