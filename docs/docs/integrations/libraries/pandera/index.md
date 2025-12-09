---
title: Dagster & Pandera
sidebar_label: Pandera
sidebar_position: 1
description: The Pandera integration library provides an API for generating Dagster Types from Pandera dataframe schemas. Like all Dagster types, Pandera-generated types can be used to annotate op inputs and outputs.
tags: [dagster-supported, metadata]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-pandera
pypi: https://pypi.org/project/dagster-pandera
sidebar_custom_props:
  logo: images/integrations/pandera.svg
partnerlink: https://pandera.readthedocs.io/en/stable/
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

<p>{frontMatter.description}</p>

Using Pandera with Dagster allows you to:

- Visualize the shape of the data by displaying dataframe structure information in the Dagster UI
- Implement runtime type-checking with rich error reporting

## Limitations

Currently, `dagster-pandera` only supports pandas and Polars dataframes, despite Pandera supporting validation on other dataframe backends.

## Prerequisites

To get started, you'll need:

- [To install](/getting-started/installation) the `dagster` and `dagster-pandera` Python packages:

  <PackageInstallInstructions packageName="dagster-pandera" />

- Familiarity with [Dagster Types](/api/dagster/types

## Usage

The `dagster-pandera` library exposes only a single public function, `pandera_schema_to_dagster_type`, which generates Dagster types from Pandera schemas. The Dagster type wraps the Pandera schema and invokes the schema's `validate()` method inside its type check function.

<CodeExample path="docs_snippets/docs_snippets/integrations/pandera/example.py" />

In the above example, we defined a toy job (`stocks_job`) with a single asset, `apple_stock_prices_dirty`. This asset returns a pandas `DataFrame` containing the opening and closing prices of Apple stock (AAPL) for a random week. The `_dirty` suffix is included because we've corrupted the data with a few random nulls.

Let's look at this job in the UI:

![Pandera job in the Dagster UI](/images/integrations/pandera/schema.png)

Notice that information from the `StockPrices` Pandera schema is rendered in the asset detail area of the right sidebar. This is possible because `pandera_schema_to_dagster_type` extracts this information from the Pandera schema and attaches it to the returned Dagster type.

If we try to run `stocks_job`, our run will fail. This is expected, as our (dirty) data contains nulls and Pandera columns are non-nullable by default. The [Dagster Typ](/api/dagster/types) returned by `pandera_schema_to_dagster_type` contains a type check function that calls `StockPrices.validate()`. This is invoked automatically on the return value of `apple_stock_prices_dirty`, leading to a type check failure.

Notice the `STEP_OUTPUT` event in the following screenshot to see Pandera's full output:

![Error report for a Pandera job in the Dagster UI](/images/integrations/pandera/error-report.png)

## About Pandera

**Pandera** is a statistical data testing toolkit, and a data validation library for scientists, engineers, and analysts seeking correctness.
