---
title: Dagster & Iceberg
sidebar_label: Iceberg
description: This library provides I/O managers for reading and writing Apache Iceberg tables. It also provides a Dagster resource for accessing Iceberg tables.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-iceberg
pypi: https://pypi.org/project/dagster-iceberg/
sidebar_custom_props:
  logo: images/integrations/iceberg.svg
  community: true
partnerlink: https://iceberg.apache.org/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-iceberg" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg.py" language="python" />

## About Apache Iceberg

**Iceberg** is a high-performance format for huge analytic tables. It brings the reliability and simplicity of SQL tables to big data, while making it possible for multiple engines to safely work with the same tables, at the same time.
