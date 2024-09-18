---
layout: Integration
status: published
name: DuckDB
title: Dagster & DuckDB
sidebar_label: DuckDB
excerpt: Read and write natively to DuckDB from Software Defined Assets.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-duckdb
docslink: https://dagster.io/blog/duckdb-data-lake
partnerlink: https://duckdb.org/
logo: /integrations/Duckdb.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

This library provides an integration with the DuckDB database, and allows for an out-of-the-box [I/O Manager](https://docs.dagster.io/concepts/io-management/io-managers) so that you can make DuckDB your storage of choice.

### Installation

```bash
pip install dagster-duckdb
```

### Example

<CodeExample filePath="integrations/duckdb.py" language="python" />

### About DuckDB

**DuckDB** is a column-oriented in-process OLAP database. A typical OLTP relational database like SQLite is row-oriented. In row-oriented database, data is organised physically as consecutive tuples.
