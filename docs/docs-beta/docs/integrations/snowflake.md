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

<CodeExample filePath="integrations/snowflake.py" language="python" />

### About Snowflake

A cloud-based data storage and analytics service, generally termed "data-as-a-service". **Snowflake**'s data warehouse is one of the most widely adopted cloud warehouses for analytics.
