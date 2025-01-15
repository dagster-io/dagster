---
layout: Integration
status: published
name: Sling
title: Dagster & Sling
sidebar_label: Sling
excerpt: Extract and load data from popular data sources to destinations with Sling through Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-sling
docslink: https://docs.dagster.io/integrations/sling
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

<CodeExample filePath="integrations/sling.py" language="python" />

### About dlt

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more.
