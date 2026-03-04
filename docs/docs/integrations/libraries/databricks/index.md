---
title: Dagster & Databricks
sidebar_label: Databricks
sidebar_position: 1
description: You can orchestrate Databricks from Dagster in multiple ways depending on your needs, including through Databricks Connect, Dagster Pipes, the Dagster Databricks Component, or Dagster Connections.
tags: [dagster-supported, compute, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-databricks
pypi: https://pypi.org/project/dagster-databricks/
sidebar_custom_props:
  logo: images/integrations/databricks.svg
partnerlink: https://databricks.com/
canonicalUrl: '/integrations/libraries/databricks'
slug: '/integrations/libraries/databricks'
---

<p>{frontMatter.description}</p>

## Choosing an integration approach

| Approach                                                                                                   | How it works                                                                                | Choose when                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **[Databricks Connect](/integrations/libraries/databricks/databricks-connect)**                            | Write Spark code in Dagster assets that executes on Databricks compute                      | <ul><li>You want to write Spark code directly in your Dagster assets</li><li>You prefer centralized code that doesn't need deployment to Databricks</li><li>You're doing interactive development or quick iterations</li><li>Your workloads are moderate in size and duration</li><li>You want simpler debugging with local code execution</li></ul>                                                                           |
| **[Dagster Pipes](/integrations/external-pipelines/databricks-pipeline)**                                  | Submit Databricks jobs and stream logs/metadata back to Dagster                             | <ul><li>You need real-time log streaming from Databricks to Dagster</li><li>Databricks job code needs to report custom metadata back to Dagster</li><li>You're running large batch jobs that should execute independently</li><li>You want fine-grained control over job submission parameters</li><li>Your code is already deployed to Databricks</li></ul>                                                                   |
| **[DatabricksAssetBundleComponent](/integrations/libraries/databricks/databricks-asset-bundle-component)** | Reads your `databricks.yml` bundle config and creates Dagster assets from job tasks         | <ul><li>Your team is using [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html)</li><li>You want Databricks job definitions version-controlled with your Dagster code</li><li>You're starting fresh or migrating jobs to a new structure</li><li>You need tight integration between job config and Dagster definitions</li><li>CI/CD pipelines manage your Databricks deployments</li></ul> |
| **[DatabricksWorkspaceComponent](/integrations/libraries/databricks/databricks-workspace-component)**      | Connects to your workspace, discovers jobs, and exposes them as Dagster assets              | <ul><li>Jobs already exist in Databricks and are managed there</li><li>You want Dagster to discover and orchestrate existing jobs</li><li>Teams manage jobs directly in Databricks UI/API</li><li>You need flexibility without maintaining local config files</li></ul>                                                                                                                                                        |
| **[Dagster Databricks Connection](/guides/labs/connections/databricks) (Dagster+ only)**                   | Automatically discover Databricks tables and catalogs as external assets in the Dagster+ UI | <ul><li>You're on Dagster+</li><li>You want visibility into Databricks tables/catalogs as external assets</li><li>Data governance and lineage tracking are priorities</li><li>You don't need to orchestrate jobs, just observe metadata</li><li>You want automatic schema and statistics extraction</li></ul>                                                                                                                  |

## About Databricks

**[Databricks](https://www.databricks.com/)** is a unified data analytics platform that simplifies and accelerates the process of building big data and AI solutions. It integrates seamlessly with [Apache Spark](https://spark.apache.org/) and offers support for various data sources and formats. Databricks provides powerful tools to create, run, and manage data pipelines, making it easier to handle complex data engineering tasks. Its collaborative and scalable environment is ideal for data engineers, scientists, and analysts who need to process and analyze large datasets efficiently.
