---
title: Dagster & Delta Lake
sidebar_label: Delta Lake
description: Delta Lake is a great storage format for Dagster workflows. With this integration, you can use the Delta Lake I/O Manager to read and write your Dagster assets.
tags: [community-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-deltalake
pypi: https://pypi.org/project/dagster-deltalake/
sidebar_custom_props:
  logo: images/integrations/deltalake.svg
  community: true
partnerlink: https://delta.io/
canonicalUrl: '/integrations/libraries/deltalake'
slug: '/integrations/libraries/deltalake'
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

Here are some of the benefits that Delta Lake provides Dagster users:

- Native PyArrow integration for lazy computation of large datasets
- More efficient querying with file skipping with Z Ordering and liquid clustering
- Built-in vacuuming to remove unnecessary files and versions
- ACID transactions for reliable writes
- Smooth versioning integration (versions can be use to trigger downstream updates).
- Surfacing table stats based on the file statistics

## Installation

<PackageInstallInstructions packageName="dagster-deltalake dagster-deltalake-pandas dagster-deltalake-polars" />

## About Delta Lake

Delta Lake is an open source storage framework that enables building a Lakehouse architecture with compute engines including Spark, PrestoDB, Flink, Trino, and Hive and APIs for Scala, Java, Rust, and Python.
