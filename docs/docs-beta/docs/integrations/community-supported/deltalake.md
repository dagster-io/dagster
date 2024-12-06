---
layout: Integration
status: published
name: Delta Lake
title: Dagster & Delta Lake
sidebar_label: Delta Lake
excerpt: Integrate your pipelines into Delta Lake.
date: 2022-11-07
communityIntegration: true
apireflink: https://delta-io.github.io/delta-rs/integrations/delta-lake-dagster/
docslink:
partnerlink: https://delta.io/
logo: /integrations/DeltaLake.svg
categories:
  - Storage
enabledBy:
enables:
---

### About this integration

Delta Lake is a great storage format for Dagster workflows. With this integration, you can use the Delta Lake I/O Manager to read and write your Dagster assets.

Here are some of the benefits that Delta Lake provides Dagster users:

- Native PyArrow integration for lazy computation of large datasets
- More efficient querying with file skipping with Z Ordering and liquid clustering
- Built-in vacuuming to remove unnecessary files and versions
- ACID transactions for reliable writes
- Smooth versioning integration (versions can be use to trigger downstream updates).
- Surfacing table stats based on the file statistics

### Installation

```bash
pip install dagster-deltalake
pip install dagster-deltalake-pandas
pip install dagster-deltalake-polars
```

### About Delta Lake

Delta Lake is an open source storage framework that enables building a Lakehouse architecture with compute engines including Spark, PrestoDB, Flink, Trino, and Hive and APIs for Scala, Java, Rust, and Python.
