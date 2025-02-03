---
layout: Integration
status: published
name: Airbyte
title: Dagster & Airbyte
sidebar_label: Airbyte
excerpt: Orchestrate Airbyte connections and schedule syncs alongside upstream or downstream dependencies.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-airbyte
docslink: https://docs.dagster.io/integrations/libraries/airbyte/airbyte-oss
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props: 
  logo: images/integrations/airbyte.svg
---

Using this integration, you can trigger Airbyte syncs and orchestrate your Airbyte connections from within Dagster, making it easy to chain an Airbyte sync with upstream or downstream steps in your workflow.

### Installation

```bash
pip install dagster-airbyte
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/airbyte.py" language="python" />

### About Airbyte

**Airbyte** is an open source data integration engine that helps you consolidate your SaaS application and database data into your data warehouses, lakes and databases.
