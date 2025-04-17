---
title: Dagster & Snowflake
sidebar_label: Snowflake
description: An integration with the Snowflake data warehouse. Read and write natively to Snowflake from Software Defined Assets.
tags: [storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-snowflake
pypi: https://pypi.org/project/dagster-snowflake/
built_by: Dagster
sidebar_custom_props:
  logo: images/integrations/snowflake.svg
partnerlink: https://www.snowflake.com/en/
---

This library provides an integration with the Snowflake data warehouse. Connect to Snowflake as a resource, then use the integration-provided functions to construct an op to establish connections and execute Snowflake queries. Read and write natively to Snowflake from Dagster assets.

### Installation

```bash
pip install dagster-snowflake
```

### Example

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake.py" language="python" />

### About Snowflake

A cloud-based data storage and analytics service, generally termed "data-as-a-service". **Snowflake**'s data warehouse is one of the most widely adopted cloud warehouses for analytics.
