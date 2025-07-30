---
title: Dagster & Polars
sidebar_label: Polars
description: The Polars integration allows using Polars eager or lazy DataFrames as inputs and outputs with Dagster’s assets and ops. Type annotations are used to control whether to load an eager or lazy DataFrame. Lazy DataFrames can be sinked as output. Multiple serialization formats (Parquet, Delta Lake, BigQuery) and filesystems (local, S3, GCS, …) are supported.
tags: [community-supported, metadata]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-polars
pypi:
sidebar_custom_props:
  logo: images/integrations/polars-logo-python.svg
  community: true
partnerlink: https://pola.rs/
---

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-polars" />

## Example

```python
import polars as pl
from dagster import asset, Definitions
from dagster_polars import PolarsParquetIOManager

@asset(io_manager_key="polars_parquet_io_manager")
def upstream():
    return DataFrame({"foo": [1, 2, 3]})

@asset(io_manager_key="polars_parquet_io_manager")
def downstream(upstream) -> pl.LazyFrame:
    assert isinstance(upstream, pl.DataFrame)
    return upstream.lazy()  # LazyFrame will be sinked


definitions = Definitions(assets=[upstream, downstream], resources={"polars_parquet_io_manager": PolarsParquetIOManager(...)})
```

Lazy pl.LazyFrame can be scanned by annotating the input with pl.LazyFrame, and returning a pl.LazyFrame will sink it:

```python
@asset(io_manager_key="polars_parquet_io_manager")
def downstream(upstream: pl.LazyFrame) -> pl.LazyFrame:
    assert isinstance(upstream, pl.LazyFrame)
    return upstream
```

Find out more in the [API docs](/api/libraries/dagster-polars)

## Supplementary

- [API docs](/api/libraries/dagster-polars)
- [Patito integration](/integrations/libraries/patito)
