---
title: Dagster & dbt Cloud (Legacy)
sidebar_label: dbt Cloud integration (Legacy)
description: Dagster allows you to run dbt Cloud jobs alongside other technologies. You can schedule them to run as a step in a larger pipeline and manage them as a data asset.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
partnerlink:
sidebar_position: 900
---

:::warning

This feature is considered superseded. While it is still available, it is no longer the best practice. For more information, see the [API lifecycle stages documentation](/api/api-lifecycle/api-lifecycle-stages).

:::

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-dbt" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_legacy.py" language="python" />

## About dbt Cloud

**dbt Cloud** is a hosted service for running dbt jobs. It helps data analysts and engineers productionize dbt deployments. Beyond dbt open source, dbt Cloud provides scheduling , CI/CD, serving documentation, and monitoring & alerting.

If you're currently using dbt Cloud™, you can also use Dagster to run `dbt-core` in its place. You can read more about [how to do that here](https://dagster.io/blog/migrate-off-dbt-cloud).
