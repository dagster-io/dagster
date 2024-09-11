---
layout: Integration
status: published
name: Snowflake
title: Dagster & Snowflake
sidebar_label: Snowflake
excerpt: An integration with the Snowflake data warehouse. Read and write natively to Snowflake from Software Defined Assets.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-snowflake
docslink: https://docs.dagster.io/integrations/snowflake
partnerlink: https://www.snowflake.com/en/
logo: /integrations/Snowflake.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

This library provides an integration with the Snowflake data warehouse. Connect to Snowflake as a resource, then use the integration-provided functions to construct an op to establish connections and execute Snowflake queries. Read and write natively to Snowflake from Dagster assets.

### Installation

```bash
pip install dagster-snowflake
```

### Example

```python
# Read the docs on Resources to learn more: https://docs.dagster.io/deployment/resources
# This integration also offers an I/O Manager. Learn more: https://docs.dagster.io/concepts/io-management/io-managers
from dagster import Definitions, EnvVar, asset
from dagster_snowflake import SnowflakeResource
import os

@asset
def my_table(snowflake: SnowflakeResource):
  with snowflake.get_connection() as conn:
    return conn.cursor().execute_query("SELECT * FROM foo")

defs = Definitions(
    assets=[my_table],
    resources={
      "snowflake": SnowflakeResource(
            account="snowflake account",
            user="snowflake user",
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="snowflake database",
            schema="snowflake schema",
            warehouse="snowflake warehouse",
        )
    }
)
```

### About Snowflake

A cloud-based data storage and analytics service, generally termed "data-as-a-service". **Snowflake**'s data warehouse is one of the most widely adopted cloud warehouses for analytics.
