---
layout: Integration
status: published
name: SDF
title: Dagster & SDF
sidebar_label: SDF
excerpt: Put your SDF transformations to work, directly from within Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-sdf
docslink: https://docs.sdf.com/integrations/dagster/getting-started
partnerlink: https://www.sdf.com/
communityIntegration: true
logo: /integrations/sdf.jpeg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

SDF can integrate seamlessly with your existing Dagster projects, providing the best-in-class transformation layer while enabling you to schedule, orchestrate, and monitor your dags in Dagster.

When it comes time to materialize your Dagster assets, you can be confident that SDF has successfully compiled your workspace, making it safe to execute locally or against your cloud data warehouse.

### Installation

```bash
pip install dagster-sdf
```

### Example

<CodeExample filePath="integrations/sdf.py" language="python" />

### About SDF

[SDF](https://www.sdf.com/) is a multi-dialect SQL compiler, transformation framework, and analytical database engine. It natively compiles SQL dialects, like Snowflake, and connects to their corresponding data warehouses to materialize models.
