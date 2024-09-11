---
layout: Integration
status: published
name: dlt
title: Dagster & dlt
sidebar_label: dlt
excerpt: Easily ingest and replicate data between systems with dlt through Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-embedded-elt
docslink: https://docs.dagster.io/integrations/embedded-elt/dlt
partnerlink: https://www.getdbt.com/
logo: /integrations/dlthub.jpeg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

This integration allows you to use [dlt](https://dlthub.com/) to easily ingest and replicate data between systems through Dagster.

### Installation

```bash
pip install dagster-embedded-elt
```

### Example

```python
import dagster as dg
from dagster_embedded_elt.dlt import DagsterDltResource, dlt_assets
from dlt import pipeline
from dlt_sources.github import github_reactions


@dlt_assets(
    dlt_source=github_reactions("dagster-io", "dagster"),
    dlt_pipeline=pipeline(
        pipeline_name="github_issues",
        dataset_name="github",
        destination="snowflake",
    ),
    name="github",
    group_name="github",
)
def github_issues_to_snowflake_assets(
    context: dg.AssetExecutionContext, dlt: DagsterDltResource
):
    yield from dlt.run(context=context)


defs = dg.Definitions(
    assets=[
        github_issues_to_snowflake_assets,
    ],
    resources={
        "dlt": DagsterDltResource(),
    },
)
```

### About dlt

[Data Load Tool (dlt)](https://dlthub.com/) is an open source library for creating efficient data pipelines. It offers features like secret management, data structure conversion, incremental updates, and pre-built sources and destinations, simplifying the process of loading messy data into well-structured datasets.
