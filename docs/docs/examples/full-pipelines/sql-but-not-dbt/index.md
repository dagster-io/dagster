---
title: SQL but not dbt pipeline
description: Learn how to build data pipelines with SQL without using dbt
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/dagster-primary-mark.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/sql-but-not-dbt'
slug: '/examples/full-pipelines/sql-but-not-dbt'
---

# Build a SQL pipeline without dbt

Sometimes you want to write SQL transformations without the overhead of learning dbt or setting up a full dbt project. This tutorial shows you how to build a data pipeline using Dagster's component system to:

- Ingest CSV files into [DuckDB](https://duckdb.org) using [Sling](https://slingdata.io/)
- Write SQL transformations directly without dbt
- Create reusable SQL components for your data transformations
- Configure everything with simple YAML files

You will learn to:

- Use Dagster's component system for data ingestion and transformation
- Create custom SQL components that can execute any SQL query
- Configure data pipelines declaratively with YAML
- Build data lineage between ingested and transformed data
- Work with DuckDB as a lightweight analytical database

## What you'll build

This pipeline demonstrates a simple e-commerce data transformation:

1. **Data ingestion**: Load raw customer, order, and payment CSV files into DuckDB tables
2. **SQL transformation**: Query the first 5 orders using a custom SQL component
3. **Component configuration**: Use YAML files to declaratively configure your pipeline

## Prerequisites

To follow the steps in this tutorial, you'll need:

- Python 3.9+ and [`uv`](https://docs.astral.sh/uv) installed
- Familiarity with Python and SQL
- Basic understanding of data pipelines

## Project structure

The project follows Dagster's component-based architecture:

```
project_sql_but_not_dbt/
├── src/sql_but_not_dbt/
│   ├── definitions.py              # Main Dagster definitions
│   ├── lib/
│   │   └── sql_component.py        # Custom SQL component implementation
│   └── defs/
│       ├── ingest_files/           # Data ingestion component
│       │   ├── component.yaml
│       │   └── replication.yaml
│       └── sql/                    # SQL transformation component
│           ├── component.yaml
│           └── first_5_orders.sql
├── raw_customers.csv               # Sample data files
├── raw_orders.csv
├── raw_payments.csv
└── pyproject.toml
```

## Key concepts

This tutorial introduces several important Dagster concepts:

- **Components**: Reusable, configurable building blocks for data pipelines
- **Declarative configuration**: Using YAML files to configure pipeline behavior
- **Asset lineage**: How Dagster tracks dependencies between data assets
- **Custom components**: Building your own components for specific use cases

## Next steps

Continue with the tutorial to learn about:

- [Data ingestion with Sling components](/examples/full-pipelines/sql-but-not-dbt/data-ingestion)
