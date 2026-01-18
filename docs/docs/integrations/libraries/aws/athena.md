---
title: Dagster & AWS Athena
sidebar_label: Athena
sidebar_position: 2
description: This integration allows you to connect to AWS Athena, a serverless interactive query service that makes it easy to analyze data in Amazon S3 using standard SQL. Using this integration, you can issue queries to Athena, fetch results, and handle query execution states within your Dagster pipelines.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-athena.svg
partnerlink: https://aws.amazon.com/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-athena.py" language="python" />

## About AWS Athena

AWS Athena is a serverless, interactive query service that allows you to analyze data directly in Amazon S3 using standard SQL. Athena is easy to use; point to your data in Amazon S3, define the schema, and start querying using standard SQL. Most results are delivered within seconds. With Athena, there are no infrastructure setups, and you pay only for the queries you run. It scales automatically—executing queries in parallel—so results are fast, even with large datasets and complex queries.
