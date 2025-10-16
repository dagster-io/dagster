---
title: Dagster & dbt Cloud
sidebar_label: dbt Cloud integration
description: Dagster allows you to run dbt Cloud jobs alongside other technologies. You can schedule them to run as a step in a larger pipeline and manage them as a data asset.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
partnerlink:
sidebar_position: 600
---

<p>{frontMatter.description}</p>

Our updated dbt Cloud integration offers two capabilities:

- **Observability** - You can view your dbt Cloud assets in the Dagster Asset Graph and double click into run/materialization history.
- **Orchestration** - You can use Dagster to schedule runs/materializations of your dbt Cloud assets, either on a cron schedule, or based on upstream dependencies.

## Installation

<PackageInstallInstructions packageName="dagster-dbt" />

## Observability example

To make use of the observability capability, you will need to add code to your Dagster project that does the following:

1. Defines your dbt Cloud credentials and workspace.
2. Uses the integration to create asset specs for models in the workspace.
3. Builds a sensor which will poll dbt Cloud for updates on runs/materialization history and dbt Cloud Assets.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_observability.py"
  language="python"
  title="defs/dbt_cloud_observability.py"
/>

## Orchestration example

To make use of the orchestration capability, you will need to add code to your Dagster project that does the following:

1. Defines your dbt Cloud credentials and workspace.
2. Builds your asset graph in a materializable way.
3. Adds these assets to the Declarative Automation Sensor.
4. Builds a sensor to poll dbt Cloud for updates on runs/materialization history and dbt Cloud Assets.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt_cloud_orchestration.py"
  language="python"
  title="defs/dbt_cloud_orchestration.py"
/>

## About dbt Cloud

**dbt Cloud** is a hosted service for running dbt jobs. It helps data analysts and engineers productionize dbt deployments. Beyond dbt open source, dbt Cloud provides scheduling , CI/CD, serving documentation, and monitoring & alerting.

If you're currently using dbt Cloud™, you can also use Dagster to run `dbt-core` in its place. You can read more about [how to do that here](https://dagster.io/blog/migrate-off-dbt-cloud).
