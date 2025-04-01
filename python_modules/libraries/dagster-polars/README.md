# dagster-polars

This library provides [Dagster](https://dagster.io/) integration with [Polars](https://pola.rs).
It allows using Polars DataFrames as inputs and outputs with Dagster's `@asset` and `@op`.
Type annotations are used to control whether to load an eager or lazy DataFrame, or other types supported by `dagster-polars`.
Multiple serialization formats (Parquet, Delta Lake, BigQuery) and filesystems (local, S3, GCS, ...) are supported.

The docs for `dagster-polars ` can be found
[here](https://docs.dagster.io/api/python-api/libraries/dagster-polars).
