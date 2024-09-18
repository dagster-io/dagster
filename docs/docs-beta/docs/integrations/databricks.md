---
layout: Integration
status: published
name: Databricks
title: Dagster & Databricks
sidebar_label: Databricks
excerpt: The Databricks integration enables you to initiate Databricks jobs directly from Dagster, seamlessly pass parameters to your code, and stream logs and structured messages back into Dagster.
date: 2024-08-20
apireflink: https://docs.dagster.io/concepts/dagster-pipes/databricks
docslink:
partnerlink: https://databricks.com/
logo: /integrations/databricks.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-databricks` integration library provides the `PipesDatabricksClient` resource, enabling you to launch Databricks jobs directly from Dagster assets and ops. This integration allows you to pass parameters to Databricks code while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.

### Installation

```bash
pip install dagster-databricks
```

### Example

<CodeExample filePath="integrations/databricks/dagster_code.py" language="python" />

<CodeExample filePath="integrations/databricks/databricks_code.py" language="python" />

### About Databricks

**Databricks** is a unified data analytics platform that simplifies and accelerates the process of building big data and AI solutions. It integrates seamlessly with Apache Spark and offers support for various data sources and formats. Databricks provides powerful tools to create, run, and manage data pipelines, making it easier to handle complex data engineering tasks. Its collaborative and scalable environment is ideal for data engineers, scientists, and analysts who need to process and analyze large datasets efficiently.
