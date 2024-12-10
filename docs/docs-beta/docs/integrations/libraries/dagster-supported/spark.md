---
layout: Integration
status: published
name: Spark
title: Dagster & Spark
sidebar_label: Spark
excerpt: Configure and run Spark jobs.
date: 2022-11-07
apireflink: https://docs.dagster.io/_apidocs/libraries/dagster-spark
docslink: https://docs.dagster.io/integrations/spark
partnerlink:
logo: /integrations/Spark.svg
categories:
  - Compute
enabledBy:
  - dagster-pyspark
enables:
---

### About this integration

Spark jobs typically execute on infrastructure that's specialized for Spark. Spark applications are typically not containerized or executed on Kubernetes.

Running Spark code often requires submitting code to a Databricks or EMR cluster. `dagster-pyspark` provides a Spark class with methods for configuration and constructing the `spark-submit` command for a Spark job.

### About Apache Spark

**Apache Spark** is an open source unified analytics engine for large-scale data processing. Spark provides an interface for programming clusters with implicit data parallelism and fault tolerance. It also provides libraries for graph computation, SQL for structured data processing, ML, and data science.
