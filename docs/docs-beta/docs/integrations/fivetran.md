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

<CodeExample filePath="integrations/fivetran.py" language="python" />

### About Fivetran

**Fivetran** ingests data from SaaS applications, databases, and servers. The data is stored and typically used for analytics.
