---
layout: Integration
status: published
name: Spark
title: Dagster & Spark
sidebar_label: Spark
excerpt: Configure and run Spark jobs.
date: 2022-11-07
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-spark
docslink: https://docs.dagster.io/integrations/libraries/spark
partnerlink:
categories:
  - Compute
enabledBy:
  - dagster-pyspark
enables:
tags: [dagster-supported, compute]
sidebar_custom_props:
  logo: images/integrations/spark.svg
---

Spark jobs typically execute on infrastructure that's specialized for Spark. Spark applications are typically not containerized or executed on Kubernetes.

Running Spark code often requires submitting code to a Databricks or EMR cluster. `dagster-pyspark` provides a Spark class with methods for configuration and constructing the `spark-submit` command for a Spark job.

### About Apache Spark

**Apache Spark** is an open source unified analytics engine for large-scale data processing. Spark provides an interface for programming clusters with implicit data parallelism and fault tolerance. It also provides libraries for graph computation, SQL for structured data processing, ML, and data science.

## Using Dagster Pipes to run Spark jobs

[Dagster pipes](/guides/build/external-pipelines/) is our toolkit for orchestrating remote compute from Dagster. It allows you to run code outside of the Dagster process, and stream logs and events back to Dagster. This is the recommended approach for running Spark jobs.

With Pipes, the code inside the asset or op definition submits a Spark job to an external system like Databricks or AWS EMR, usually pointing to a jar or zip of Python files that contain the actual Spark data transformations and actions.

You can either use one of the available Pipes Clients or make your own. The available Pipes Clients for popular Spark providers are:

- [Databricks](/guides/build/external-pipelines/databricks-pipeline)
- [AWS Glue](/guides/build/external-pipelines/aws/aws-glue-pipeline)
- [AWS EMR](/guides/build/external-pipelines/aws/aws-emr-pipeline)
- [AWS EMR on EKS](/guides/build/external-pipelines/aws/aws-emr-containers-pipeline)
- [AWS EMR Serverless](/guides/build/external-pipelines/aws/aws-emr-serverless-pipeline)

Existing Spark jobs can be used with Pipes without any modifications. In this case, Dagster will be receiving logs from the job, but not events like asset checks or attached metadata.

Additionally, it's possible to send events to Dagster from the job by utilizing the `dagster_pipes` module. This requires minimal code changes on the job side.

This approach also works for Spark jobs written in Java or Scala, although we don't have Pipes implementations for emitting events from those languages yet.
