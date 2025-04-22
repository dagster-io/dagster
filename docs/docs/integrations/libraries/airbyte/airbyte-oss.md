---
title: Dagster & Airbyte
sidebar_label: Airbyte
description: Orchestrate Airbyte connections and schedule syncs alongside upstream or downstream dependencies.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte
pypi: https://pypi.org/project/dagster-airbyte/
sidebar_custom_props:
  logo: images/integrations/airbyte.svg
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
---

Using this integration, you can trigger Airbyte syncs and orchestrate your Airbyte connections from within Dagster, making it easy to chain an Airbyte sync with upstream or downstream steps in your workflow.

### Installation

```bash
pip install dagster-airbyte
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/airbyte.py" language="python" />

### About Airbyte

**Airbyte** is an open source data integration engine that helps you consolidate your SaaS application and database data into your data warehouses, lakes and databases.
