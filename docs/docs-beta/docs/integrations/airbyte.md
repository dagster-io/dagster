---
layout: Integration
status: published
name: Airbyte
title: Dagster & Airbyte
sidebar_label: Airbyte
excerpt: Orchestrate Airbyte connections and schedule syncs alongside upstream or downstream dependencies.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-airbyte
docslink: https://docs.dagster.io/integrations/airbyte
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
logo: /integrations/airbyte.svg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

Using this integration, you can trigger Airbyte syncs and orchestrate your Airbyte connections from within Dagster, making it easy to chain an Airbyte sync with upstream or downstream steps in your workflow.

### Installation

```bash
pip install dagster-airbyte
```

### Example

```python
from dagster import EnvVar
from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance
import os

# Connect to your OSS Airbyte instance
airbyte_instance = AirbyteResource(
    host="localhost",
    port="8000",
    # If using basic auth, include username and password:
    username="airbyte",
    password=EnvVar("AIRBYTE_PASSWORD")
)

# Load all assets from your Airbyte instance
airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)

```

### About Airbyte

**Airbyte** is an open source data integration engine that helps you consolidate your SaaS application and database data into your data warehouses, lakes and databases.
