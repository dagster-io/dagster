---
layout: Integration
status: published
name: Pandera
title: Dagster & Pandera
sidebar_label: Pandera
excerpt: Generate Dagster Types from Pandera dataframe schemas.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-pandera
docslink: https://docs.dagster.io/integrations/pandera
partnerlink: https://pandera.readthedocs.io/en/stable/
categories:
  - Metadata
enabledBy:
enables:
tags: [dagster-supported, metadata]
sidebar_custom_props:
  logo: images/integrations/pandera.svg
---

The `dagster-pandera` integration library provides an API for generating Dagster Types from [Pandera DataFrame schemas](https://pandera.readthedocs.io/en/stable/dataframe_schemas.html).

Like all Dagster types, Dagster-Pandera-generated types can be used to annotate op inputs and outputs. This provides runtime type-checking with rich error reporting and allows Dagster UI to display information about a DataFrame's structure.

:::note

Currently, `dagster-pandera` only supports pandas and Polars dataframes, despite Pandera supporting validation on other dataframe backends.

:::

### Installation

```bash
pip install dagster-pandera
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/pandera.py" language="python" />

### About Pandera

**Pandera** is a statistical data testing toolkit, and a data validation library for scientists, engineers, and analysts seeking correctness.
