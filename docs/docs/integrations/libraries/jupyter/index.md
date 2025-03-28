---
layout: Integration
status: published
name: Jupyter Notebooks
title: Dagster & Jupyter Notebooks
sidebar_label: Jupyter Notebooks
excerpt: Dagstermill eliminates the tedious "productionization" of Jupyter notebooks.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagstermill
docslink: https://docs.dagster.io/integrations/libraries/dagstermill
partnerlink:
enabledBy:
  - dagster-dagstermill
categories:
  - Compute
enables:
tags: [dagster-supported, compute]
sidebar_custom_props:
  logo: images/integrations/jupyter.svg
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

Dagstermill eliminates the tedious "productionization" of Jupyter notebooks.

Using the Dagstermill library enables you to:

- View notebooks directly in the Dagster UI without needing to set up a Jupyter kernel
- Define data dependencies to flow inputs and outputs from assets/ops to notebooks, between notebooks, and from notebooks to other assets/ops
- Use Dagster resources and the Dagster config system inside notebooks
- Aggregate notebook logs with logs from other Dagster assets and ops
- Yield custom materializations and other Dagster events from your notebook code

### About Jupyter

Fast iteration, the literate combination of arbitrary code with markdown blocks, and inline plotting make notebooks an indispensable tool for data science. The **Dagstermill** package makes it easy to run notebooks using the Dagster tools and to integrate them into data jobs with heterogeneous ops: for instance, Spark jobs, SQL statements run against a data warehouse, or arbitrary Python code.
