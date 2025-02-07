---
layout: Integration
status: published
name: Sling
title: Dagster & Sling
sidebar_label: Sling
excerpt: Extract and load data from popular data sources to destinations with Sling through Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-sling
docslink: https://docs.dagster.io/integrations/libraries/sling
partnerlink: https://slingdata.io/
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props:
  logo: images/integrations/sling.png
---

This integration allows you to use [Sling](https://slingdata.io/) to extract and load data from popular data sources to destinations with high performance and ease.

### Installation

```bash
pip install dagster-sling
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/sling.py" language="python" />

### About Sling

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more. 

#### Key Features

- **Data Movement**: Transfer data between different storage systems and databases efficiently

- **Flexible Connectivity**: Support for numerous databases, data warehouses, and file storage systems

- **Transformation Capabilities**: Built-in data transformation features during transfer

- **Multiple Operation Modes**: Support for various replication modes including full-refresh, incremental, and snapshot

- **Production-Ready**: Deployable with monitoring, scheduling, and error handling
