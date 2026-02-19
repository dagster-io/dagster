---
title: Dagster & Iceberg
sidebar_label: Iceberg
sidebar_position: 1
description: This library provides I/O managers for reading and writing Apache Iceberg tables. It also provides a Dagster resource for accessing Iceberg tables.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-iceberg
pypi: https://pypi.org/project/dagster-iceberg/
sidebar_custom_props:
  logo: images/integrations/iceberg.svg
  community: true
partnerlink: https://iceberg.apache.org/
canonicalUrl: '/integrations/libraries/iceberg'
slug: '/integrations/libraries/iceberg'
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-iceberg" />

The [`dagster-iceberg` library](/integrations/libraries/iceberg/dagster-iceberg) defines the following extras for interoperability with various DataFrame libraries:

- `daft` for interoperability with Daft DataFrames
- `pandas` for interoperability with pandas DataFrames
- `polars` for interoperability with Polars DataFrames
- `spark` for interoperability with PySpark DataFrames (specifically, via Spark Connect)

`pyarrow` is a core package dependency, so the <PyObject section="libraries" integration="iceberg" object="io_manager.arrow.PyArrowIcebergIOManager" module="dagster_iceberg" /> is always available.

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg.py" language="python" />

## About Apache Iceberg

**Iceberg** is a high-performance format for huge analytic tables. It brings the reliability and simplicity of SQL tables to big data, while making it possible for multiple engines to safely work with the same tables, at the same time.
