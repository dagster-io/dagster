---
title: Dagster & Databricks
sidebar_label: Databricks
description: The Databricks integration library provides the `PipesDatabricksClient` resource, enabling you to launch Databricks jobs directly from Dagster assets and ops. This integration allows you to pass parameters to Databricks code while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-databricks
pypi: https://pypi.org/project/dagster-databricks/
sidebar_custom_props:
  logo: images/integrations/databricks.svg
partnerlink: https://databricks.com/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-databricks" />

## All-purpose compute example

<CodeExample path="docs_snippets/docs_snippets/integrations/databricks/dagster_code.py" language="python" />

<CodeExample path="docs_snippets/docs_snippets/integrations/databricks/databricks_code.py" language="python" />

## Serverless compute example

Using pipes with Databricks serverless compute is slightly different. First, you can't specify library dependencies, you must instead define dagster-pipes as a dependency in the notebook environment.

Second, You must use Volumes for context loading and message writing, since dbfs is incompatible with serverless compute.

<CodeExample path="docs_snippets/docs_snippets/integrations/databricks/dagster_code_serverless.py" language="python" />

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_code_serverless.py"
  language="python"
/>

## About Databricks

**Databricks** is a unified data analytics platform that simplifies and accelerates the process of building big data and AI solutions. It integrates seamlessly with Apache Spark and offers support for various data sources and formats. Databricks provides powerful tools to create, run, and manage data pipelines, making it easier to handle complex data engineering tasks. Its collaborative and scalable environment is ideal for data engineers, scientists, and analysts who need to process and analyze large datasets efficiently.
