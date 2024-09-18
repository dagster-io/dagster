---
layout: Integration
status: published
name: dbt Cloud
title: Dagster & dbt Cloud
sidebar_label: dbt Cloud
excerpt: Run dbt Cloud™ jobs as part of your data pipeline.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-dbt#assets-dbt-cloud
docslink: https://docs.dagster.io/integrations/dbt_cloud
partnerlink:
logo: /integrations/dbt.svg
categories:
  - ETL
enabledBy:
enables:
---

### About this integration

Dagster allows you to run dbt Cloud jobs alongside other technologies. You can schedule them to run as a step in a larger pipeline and manage them as a data asset.

### Installation

```bash
pip install dagster-dbt
```

### Example

<CodeExample filePath="integrations/dbt_cloud.py" language="python" />

### About dbt Cloud

**dbt Cloud** is a hosted service for running dbt jobs. It helps data analysts and engineers productionize dbt deployments. Beyond dbt open source, dbt Cloud provides scheduling , CI/CD, serving documentation, and monitoring & alerting.

If you're currently using dbt Cloud™, you can also use Dagster to run `dbt-core` in its place. You can read more about [how to do that here](https://dagster.io/blog/migrate-off-dbt-cloud).
