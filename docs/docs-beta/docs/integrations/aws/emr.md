---
layout: Integration
status: published
name: EMR
title: Dagster & AWS EMR
sidebar_label: EMR
excerpt: The AWS EMR integration allows you to seamlessly integrate AWS EMR into your Dagster pipelines for petabyte-scale data processing using open source tools like Apache Spark, Hive, Presto, and more.
date: 2024-06-21
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-aws
docslink:
partnerlink: https://aws.amazon.com/
logo: /integrations/aws-emr.svg
categories:
  - Compute
enabledBy:
enables:
---

### About this integration

The `dagster-aws` integration provides ways orchestrating data pipelines that leverage AWS services, including AWS EMR (Elastic MapReduce). This integration allows you to run and scale big data workloads using open source tools such as Apache Spark, Hive, Presto, and more.

Using this integration, you can:

- Seamlessly integrate AWS EMR into your Dagster pipelines.
- Utilize EMR for petabyte-scale data processing.
- Easily manage and monitor EMR clusters and jobs from within Dagster.
- Leverage Dagster's orchestration capabilities to handle complex data workflows involving EMR.

### Installation

```bash
pip install dagster-aws
```

### Examples

<CodeExample filePath="integrations/aws-emr.py" language="python" />

### About AWS EMR

**AWS EMR** (Elastic MapReduce) is a cloud big data platform for processing vast amounts of data using open source tools such as Apache Spark, Apache Hive, Apache HBase, Apache Flink, Apache Hudi, and Presto. It simplifies running big data frameworks, allowing you to process and analyze large datasets quickly and cost-effectively. AWS EMR provides the scalability, flexibility, and reliability needed to handle complex data processing tasks, making it an ideal choice for data engineers and scientists.
