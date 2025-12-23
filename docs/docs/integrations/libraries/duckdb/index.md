---
title: Dagster & DuckDB
sidebar_label: DuckDB
sidebar_position: 1
description: This library provides an integration with the DuckDB database, and allows for an out-of-the-box I/O Manager so that you can make DuckDB your storage of choice.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-duckdb
pypi: https://pypi.org/project/dagster-duckdb/
sidebar_custom_props:
  logo: images/integrations/duckdb.svg
partnerlink: https://duckdb.org/
canonicalUrl: '/integrations/libraries/duckdb'
slug: '/integrations/libraries/duckdb'
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-duckdb" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb.py" language="python" />

## About DuckDB

**DuckDB** is a column-oriented in-process OLAP database. A typical OLTP relational database like SQLite is row-oriented. In row-oriented database, data is organised physically as consecutive tuples.
