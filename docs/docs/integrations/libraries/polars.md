---
layout: Integration
status: published
name: Polars
title: Dagster & Polars
sidebar_label: Polars
excerpt: The Polars data processing library is supported by [dagster-polars](/integrations/polars)
date: 2025-03-14
apireflink:
docslink: https://docs.dagster.io/integrations/libraries/polars
partnerlink: https://pola.rs/
categories:
- Compute
- Metadata
enabledBy:
enables:
tags: [dagster-supported, metadata]
sidebar_custom_props:
  logo: images/integrations/polars-logo-python.svg
---

Polars is a blazingly fast DataFrame library written in Rust with bindings for Python.

The `dagster-polars` integration allows using Polars eager or lazy DataFrames as inputs and outputs with Dagster’s assets and ops. Type annotations are used to control whether to load an eager or lazy DataFrame. Lazy DataFrames can be sinked as output. Multiple serialization formats (Parquet, Delta Lake, BigQuery) and filesystems (local, S3, GCS, …) are supported.

`dagster-polars` integrates with [Patito](https://github.com/JakobGM/patito) for data validation. Learn more on the [Patito integration page](/integrations/libraries/patito).

## Installation
```shell
pip install dagster-polars
```

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


definitions = Definitions(assets=[upstrea, downstream], resources={"polars_parquet_io_manager": PolarsParquetIOManager(...)})
```

Lazy pl.LazyFrame can be scanned by annotating the input with pl.LazyFrame, and returning a pl.LazyFrame will sink it:

```python
@asset(io_manager_key="polars_parquet_io_manager")
def downstream(upstream: pl.LazyFrame) -> pl.LazyFrame:
    assert isinstance(upstream, pl.LazyFrame)
    return upstream
```

Find out more in the [API docs](/api/python-api/libraries/dagster-polars)

## Supplementary

- [API docs](/api/python-api/libraries/dagster-polars)
- [Patito integration](/integrations/libraries/patito)
