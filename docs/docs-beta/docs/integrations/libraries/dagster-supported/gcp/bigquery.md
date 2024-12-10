---
layout: Integration
status: published
name: BigQuery
title: Dagster & GCP BigQuery
sidebar_label: BigQuery
excerpt: Integrate with GCP BigQuery.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-gcp
docslink:
partnerlink:
logo: /integrations/gcp-bigquery.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

The Google Cloud Platform BigQuery integration allows data engineers to easily query and store data in the BigQuery data warehouse through the use of the `BigQueryResource`.

### Installation

```bash
pip install dagster-gcp
```

### Examples

<CodeExample filePath="integrations/gcp-bigquery.py" language="python" />

### About Google Cloud Platform BigQuery

The Google Cloud Platform BigQuery service, offers a fully managed enterprise data warehouse that enables fast SQL queries using the processing power of Google's infrastructure.
