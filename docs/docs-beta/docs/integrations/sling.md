---
layout: Integration
status: published
name: Sling
title: Dagster & Sling
sidebar_label: Sling
excerpt: Extract and load data from popular data sources to destinations with Sling through Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-embedded-elt
docslink: https://docs.dagster.io/integrations/embedded-elt/sling
partnerlink: https://slingdata.io/
logo: /integrations/sling.png
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

This integration allows you to use [Sling](https://slingdata.io/) to extract and load data from popular data sources to destinations with high performance and ease.

### Installation

```bash
pip install dagster-embedded-elt
```

### Example

<CodeExample filePath="integrations/sling.py" language="python" />

### About dlt

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more.
