---
title: Dagster & Pandas
sidebar_label: Pandas
description: Implement validation on pandas DataFrames.
tags: [dagster-supported, metadata]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-pandas
pypi: https://pypi.org/project/dagster-pandas
sidebar_custom_props:
  logo: images/integrations/pandas.svg
partnerlink: https://pandas.pydata.org/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

:::note

This page describes the `dagster-pandas` library, which is used for performing data validation. To simply use pandas with Dagster, start with the [Dagster Quickstart](/getting-started/quickstart).

Dagster makes it easy to use pandas code to manipulate data and then store
that data in other systems such as [files on Amazon S3](/api/libraries/dagster-aws#dagster_aws.s3.s3_pickle_io_manager) or [tables in Snowflake](/integrations/libraries/snowflake/using-snowflake-with-dagster)

:::

- [Creating Dagster DataFrame Types](#creating-dagster-dataframe-types)
- [Dagster DataFrame Level Validation](#dagster-dataframe-level-validation)
- [Dagster DataFrame Summary Statistics](#dagster-dataframe-summary-statistics)

The `dagster_pandas` library provides the ability to perform data validation, emit summary statistics, and enable reliable dataframe serialization/deserialization. On top of this, the Dagster type system generates documentation of your dataframe constraints and makes it accessible in the Dagster UI.

## Creating Dagster DataFrame Types

To create a custom `dagster_pandas` type, use `create_dagster_pandas_dataframe_type` and provide a list of `PandasColumn` objects which specify column-level schema and constraints. For example, we can construct a custom dataframe type to represent a set of e-bike trips in the following way:

<CodeExample
  path="docs_snippets/docs_snippets/legacy/dagster_pandas_guide/core_trip.py"
  startAfter="start_core_trip_marker_0"
  endBefore="end_core_trip_marker_0"
/>

Once our custom data type is defined, we can use it as the type declaration for the inputs / outputs of our ops:

<CodeExample
  path="docs_snippets/docs_snippets/legacy/dagster_pandas_guide/core_trip.py"
  startAfter="start_core_trip_marker_1"
  endBefore="end_core_trip_marker_1"
/>

By passing in these `PandasColumn` objects, we are expressing the schema and constraints we expect our dataframes to follow when Dagster performs type checks for our ops. Moreover, if we go to the op viewer, we can follow our schema documented in the UI:

![tutorial2](/images/integrations/pandas/tutorial2.png)

## Dagster DataFrame Level Validation

Now that we have a custom dataframe type that performs schema validation during a run, we can express dataframe level constraints (e.g number of rows, or columns).

To do this, we provide a list of dataframe constraints to `create_dagster_pandas_dataframe_type`; for example, using `RowCountConstraint`. More information on the available constraints can be found in the `dagster_pandas` [API docs](/api/libraries/dagster-pandas).

This looks like:

<CodeExample
  path="docs_snippets/docs_snippets/legacy/dagster_pandas_guide/shape_constrained_trip.py"
  startAfter="start_create_type"
  endBefore="end_create_type"
/>

If we rerun the above example with this dataframe, nothing should change. However, if we pass in 100 to the row count constraint, we can watch our job fail that type check.

## Dagster DataFrame Summary Statistics

Aside from constraint validation, `create_dagster_pandas_dataframe_type` also takes in a summary statistics function that emits metadata dictionaries which are surfaced during runs. Since data systems seldom control the quality of the data they receive, it becomes important to monitor data as it flows through your systems. In complex jobs, this can help debug and monitor data drift over time. Let's illustrate how this works in our example:

<CodeExample
  path="docs_snippets/docs_snippets/legacy/dagster_pandas_guide/summary_stats.py"
  startAfter="start_summary"
  endBefore="end_summary"
/>

Now if we run this job in the UI launchpad, we can see that the `SummaryStatsTripDataFrame` type is displayed in the logs along with the emitted metadata.

![tutorial1.png](/images/integrations/pandas/tutorial1.png)

## Dagster DataFrame Custom Validation

`PandasColumn` is user-pluggable with custom constraints. They can be constructed directly and passed a list of `ColumnConstraint` objects.

To tie this back to our example, let's say that we want to validate that the amount paid for a e-bike must be in 5 dollar increments because that is the price per mile rounded up. As a result, let's implement a `DivisibleByFiveConstraint`. To do this, all it needs is a `markdown_description` for the UI which accepts and renders markdown syntax, an `error_description` for error logs, and a validation method which throws a `ColumnConstraintViolationException` if a row fails validation. This would look like the following:

<CodeExample
  path="docs_snippets/docs_snippets/legacy/dagster_pandas_guide/custom_column_constraint.py"
  startAfter="start_custom_col"
  endBefore="end_custom_col"
/>

## About Pandas

**Pandas** is a popular Python package that provides data structures designed to make working with "relational" or "labeled" data both easy and intuitive. Pandas aims to be the fundamental high-level building block for doing practical, real-world data analysis in Python.
