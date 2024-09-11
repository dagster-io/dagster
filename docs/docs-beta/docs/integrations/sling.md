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

```python
import dagster as dg
from dagster_embedded_elt.sling import (
    SlingConnectionResource,
    SlingResource,
    sling_assets,
)

source = SlingConnectionResource(
    name="MY_PG",
    type="postgres",
    host="localhost",
    port=5432,
    database="my_database",
    user="my_user",
    password=dg.EnvVar("PG_PASS"),
)

target = SlingConnectionResource(
    name="MY_SF",
    type="snowflake",
    host="hostname.snowflake",
    user="username",
    database="database",
    password=dg.EnvVar("SF_PASSWORD"),
    role="role",
)


@sling_assets(
    replication_config={
        "SOURCE": "MY_PG",
        "TARGET": "MY_SF",
        "defaults": {
            "mode": "full-refresh",
            "object": "{stream_schema}_{stream_table}",
        },
        "streams": {
            "public.accounts": None,
            "public.users": None,
            "public.finance_departments": {"object": "departments"},
        },
    }
)
def sling_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)


defs = dg.Definitions(
    assets=[sling_assets],
    resources={
        "sling": SlingResource(
            connections=[
                source,
                target,
            ]
        )
    },
)
```

### About dlt

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more.
