---
layout: Integration
status: published
name: DuckDB
title: Dagster & DuckDB
sidebar_label: DuckDB
excerpt: Read and write natively to DuckDB from Software Defined Assets.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-duckdb
docslink: https://docs.dagster.io/integrations/libraries/duckdb/
partnerlink: https://duckdb.org/
categories:
  - Storage
enabledBy:
enables:
tags: [dagster-supported, storage]
sidebar_custom_props:
  logo: images/integrations/duckdb.svg
---

This library provides an integration with the DuckDB database, and allows for an out-of-the-box [I/O Manager](/guides/build/io-managers/) so that you can make DuckDB your storage of choice.

### Installation

```bash
pip install dagster-duckdb
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb.py" language="python" />

### About DuckDB

**DuckDB** is a column-oriented in-process OLAP database. A typical OLTP relational database like SQLite is row-oriented. In row-oriented database, data is organised physically as consecutive tuples.
