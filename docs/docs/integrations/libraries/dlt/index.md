---
layout: Integration
status: published
name: dlt
title: Dagster & dlt
sidebar_label: dlt
excerpt: Easily ingest and replicate data between systems with dlt through Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-dlt
docslink: https://docs.dagster.io/integrations/libraries/dlt/
partnerlink: https://dlthub.com/
logo: /integrations/dlthub.jpeg
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props:
  logo: images/integrations/dlthub.jpeg
---

This integration allows you to use [dlt](https://dlthub.com/) to easily ingest and replicate data between systems through Dagster.

### Installation

```bash
pip install dagster-dlt
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/dlt.py" language="python" />

:::note

If you are using the [sql_database](https://dlthub.com/docs/api_reference/sources/sql_database/__init__#sql_database) source, consider setting `defer_table_reflect=True` to reduce database reads. By default, the Dagster daemon will refresh definitions roughly every minute, which will query the database for resource definitions.

:::

### About dlt

[Data Load Tool (dlt)](https://dlthub.com/) is an open source library for creating efficient data pipelines. It offers features like secret management, data structure conversion, incremental updates, and pre-built sources and destinations, simplifying the process of loading messy data into well-structured datasets.
