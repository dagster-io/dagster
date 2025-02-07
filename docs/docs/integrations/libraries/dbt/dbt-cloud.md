---
layout: Integration
status: published
name: dbt Cloud
title: Dagster & dbt Cloud
sidebar_label: dbt Cloud
excerpt: Run dbt Cloud™ jobs as part of your data pipeline.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-dbt#assets-dbt-cloud
docslink: https://docs.dagster.io/integration/libraries/dbt/dbt_cloud
partnerlink:
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props: 
  logo: images/integrations/dbt/dbt.svg
---

import Beta from '../../../partials/\_Beta.md';

<Beta />

Dagster allows you to run dbt Cloud jobs alongside other technologies. You can schedule them to run as a step in a larger pipeline and manage them as a data asset.

### Installation

```bash
pip install dagster-dbt
```

### Example

<CodeExample path="docs_beta_snippets/docs_beta_snippets/integrations/dbt_cloud.py" language="python" />

### About dbt Cloud

**dbt Cloud** is a hosted service for running dbt jobs. It helps data analysts and engineers productionize dbt deployments. Beyond dbt open source, dbt Cloud provides scheduling , CI/CD, serving documentation, and monitoring & alerting.

If you're currently using dbt Cloud™, you can also use Dagster to run `dbt-core` in its place. You can read more about [how to do that here](https://dagster.io/blog/migrate-off-dbt-cloud).
