---
title: Dagster & AWS EMR
sidebar_label: EMR
sidebar_position: 5
description: The AWS integration provides ways orchestrating data pipelines that leverage AWS services, including AWS EMR (Elastic MapReduce). This integration allows you to run and scale big data workloads using open source tools such as Apache Spark, Hive, Presto, and more.
tags: [dagster-supported, compute]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-aws
pypi: https://pypi.org/project/dagster-aws/
sidebar_custom_props:
  logo: images/integrations/aws-emr.svg
partnerlink: https://aws.amazon.com/
---

<p>{frontMatter.description}</p>

Using this integration, you can:

- Seamlessly integrate AWS EMR into your Dagster pipelines.
- Utilize EMR for petabyte-scale data processing.
- Easily manage and monitor EMR clusters and jobs from within Dagster.
- Leverage Dagster's orchestration capabilities to handle complex data workflows involving EMR.

## Installation

<PackageInstallInstructions packageName="dagster-aws" />

## Examples

<CodeExample path="docs_snippets/docs_snippets/integrations/aws-emr.py" language="python" />

## About AWS EMR

**AWS EMR** (Elastic MapReduce) is a cloud big data platform for processing vast amounts of data using open source tools such as Apache Spark, Apache Hive, Apache HBase, Apache Flink, Apache Hudi, and Presto. It simplifies running big data frameworks, allowing you to process and analyze large datasets quickly and cost-effectively. AWS EMR provides the scalability, flexibility, and reliability needed to handle complex data processing tasks, making it an ideal choice for data engineers and scientists.
