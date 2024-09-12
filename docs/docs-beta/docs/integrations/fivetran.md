---
layout: Integration
status: published
name: Fivetran
title: Dagster & Fivetran
sidebar_label: Fivetran
excerpt: Orchestrate Fivetran connectors and schedule syncs with upstream or downstream dependencies.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-fivetran
docslink: https://docs.dagster.io/integrations/fivetran
partnerlink: https://www.fivetran.com/
logo: /integrations/Fivetran.svg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

The Dagster-Fivetran integration enables you to orchestrate data ingestion as part of a larger pipeline. Programmatically interact with the Fivetran REST API to initiate syncs and monitor their progress.

### Installation

```bash
pip install dagster-fivetran
```

### Example

```python
from dagster import EnvVar
from dagster_fivetran import FivetranResource, load_assets_from_fivetran_instance
import os

fivetran_instance = FivetranResource(
    api_key="some_key",
    api_secret=EnvVar("FIVETRAN_SECRET"),
)
fivetran_assets = load_assets_from_fivetran_instance(fivetran_instance)
```

### About Fivetran

**Fivetran** ingests data from SaaS applications, databases, and servers. The data is stored and typically used for analytics.
