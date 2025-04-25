---
title: Dagster & dbt Cloud
sidebar_label: dbt Cloud
description: Run dbt Cloud™ jobs as part of your data pipeline.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
partnerlink:
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

Dagster allows you to run dbt Cloud jobs alongside other technologies. You can schedule them to run as a step in a larger pipeline and manage them as a data asset.

## Installation

<PackageInstallInstructions packageName="dagster-dbt" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt_cloud.py" language="python" />

## About dbt Cloud

**dbt Cloud** is a hosted service for running dbt jobs. It helps data analysts and engineers productionize dbt deployments. Beyond dbt open source, dbt Cloud provides scheduling , CI/CD, serving documentation, and monitoring & alerting.

If you're currently using dbt Cloud™, you can also use Dagster to run `dbt-core` in its place. You can read more about [how to do that here](https://dagster.io/blog/migrate-off-dbt-cloud).
