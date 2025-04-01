---
layout: Integration
status: published
name: Embedded ELT
title: Dagster & Embedded ELT
sidebar_label: Embedded ELT
excerpt: Build ELT pipelines with Dagster through helpful asset decorators and resources
date:
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-embedded-elt
docslink: https://docs.dagster.io/integrations/libraries/embedded-elt
partnerlink:
categories:
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props:
  logo: images/integrations/sling.png
---

The `dagster-embedded-elt` package provides a framework for building ELT pipelines with Dagster through helpful asset decorators and resources. It includes the `dagster-dlt` and `dagster-sling` packages, which you can also use on their own. To get started,

This package includes two integrations:

- [Sling](https://slingdata.io) provides a simple way to sync data between databases and file systems.
- [data Load Tool (dlt)](https://dlthub.com) easily loads data from external systems and APIs.

## Installation

```bash
pip install dagster-embedded-elt
```

## Sling

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more. The Dagster integration allows you to derive Dagster assets from a replication configuration file.

For more information, see the [Sling integration docs](/integrations/libraries/sling).

## dlt

With the ability to leverage pre-made [verified sources](https://dlthub.com/docs/dlt-ecosystem/verified-sources/) like [Hubspot](https://dlthub.com/docs/dlt-ecosystem/verified-sources/hubspot) and [Notion](https://dlthub.com/docs/dlt-ecosystem/verified-sources/notion), and [destinations](https://dlthub.com/docs/dlt-ecosystem/destinations/) like [Databricks](https://dlthub.com/docs/dlt-ecosystem/destinations/databricks) and [Snowflake](https://dlthub.com/docs/dlt-ecosystem/destinations/snowflake), integrating dlt into your Dagster project enables you to load a data in an easy and structured way.

For more information, see the [dlt integration docs](/integrations/libraries/dlt).
