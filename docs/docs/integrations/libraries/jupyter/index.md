---
title: Dagster & Jupyter Notebooks
sidebar_label: Jupyter Notebooks
description: Dagstermill eliminates the tedious "productionization" of Jupyter notebooks.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagstermill
pypi: https://pypi.org/project/dagstermill/
sidebar_custom_props:
  logo: images/integrations/jupyter.svg
partnerlink:
canonicalUrl: '/integrations/libraries/jupyter'
slug: '/integrations/libraries/jupyter'
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

Using the Dagstermill library enables you to:

- View notebooks directly in the Dagster UI without needing to set up a Jupyter kernel
- Define data dependencies to flow inputs and outputs from assets/ops to notebooks, between notebooks, and from notebooks to other assets/ops
- Use Dagster resources and the Dagster config system inside notebooks
- Aggregate notebook logs with logs from other Dagster assets and ops
- Yield custom materializations and other Dagster events from your notebook code

## About Jupyter

Fast iteration, the literate combination of arbitrary code with markdown blocks, and inline plotting make notebooks an indispensable tool for data science. The **Dagstermill** package makes it easy to run notebooks using the Dagster tools and to integrate them into data jobs with heterogeneous ops: for instance, Spark jobs, SQL statements run against a data warehouse, or arbitrary Python code.
