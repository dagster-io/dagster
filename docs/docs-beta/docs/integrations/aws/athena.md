---
layout: Integration
status: published
name: Athena
title: Dagster & AWS Athena
sidebar_label: Athena
excerpt: This integration allows you to connect to AWS Athena and analyze data in Amazon S3 using standard SQL within your Dagster pipelines.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink:
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-athena.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

This integration allows you to connect to AWS Athena, a serverless interactive query service that makes it easy to analyze data in Amazon S3 using standard SQL. Using this integration, you can issue queries to Athena, fetch results, and handle query execution states within your Dagster pipelines.

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample filePath="integrations/aws-athena.py" language="python" />

### About AWS Athena

AWS Athena is a serverless, interactive query service that allows you to analyze data directly in Amazon S3 using standard SQL. Athena is easy to use; point to your data in Amazon S3, define the schema, and start querying using standard SQL. Most results are delivered within seconds. With Athena, there are no infrastructure setups, and you pay only for the queries you run. It scales automatically—executing queries in parallel—so results are fast, even with large datasets and complex queries.
