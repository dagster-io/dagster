---
title: Dagster & AWS Glue
sidebar_label: Glue
sidebar_position: 6
description: The AWS integration library provides the PipesGlueClient resource, enabling you to launch AWS Glue jobs directly from Dagster assets and ops. This integration allows you to pass parameters to Glue code while Dagster receives real-time events, such as logs, asset checks, and asset materializations, from the initiated jobs. With minimal code changes required on the job side, this integration is both efficient and easy to implement.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-glue.svg
partnerlink: https://aws.amazon.com/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-glue.py" language="python" />

## About AWS Glue

**AWS Glue** is a fully managed cloud service designed to simplify and automate the process of discovering, preparing, and integrating data for analytics, machine learning, and application development. It supports a wide range of data sources and formats, offering seamless integration with other AWS services. AWS Glue provides the tools to create, run, and manage ETL (Extract, Transform, Load) jobs, making it easier to handle complex data workflows. Its serverless architecture allows for scalability and flexibility, making it a preferred choice for data engineers and analysts who need to process and prepare data efficiently.
