---
title: "Unit testing assets and ops"
sidebar_position: 400
---

Unit testing is essential for ensuring that computations function as intended. In the context of data pipelines, this can be particularly challenging. However, Dagster streamlines the process by enabling direct invocation of computations with specified input values and mocked resources, making it easier to verify that data transformations behave as expected.

While unit tests can't fully replace integration tests or manual review, they can catch a variety of errors with a significantly faster feedback loop.

This article covers how to write unit tests for assets with a variety of different input requirements.

:::note

Before you begin implementing unit tests, note that:

- Testing individual assets is generally recommended over unit testing entire jobs.
- Unit testing isn't recommended in cases where most of the business logic is encoded in an external system, such as an asset which directly invokes an external Databricks job.
- If you want to test your assets at runtime, you can use [asset checks](asset-checks) to verify the quality of data produced by your pipelines, communicate what the data is expected to do, and more.

:::

## Unit test examples

### Assets and ops without arguments \{#no-arguments}

The simplest assets to test are those with no arguments. In these cases, you can directly invoke definitions.

<CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-no-argument.py" language="python"/>

### Assets with upstream dependencies \{#upstream-dependencies}

If an asset has an upstream dependency, you can directly pass a value for that dependency when invoking the definition.

<CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-dependency.py" language="python" />

### Assets with config \{#config}

If an asset uses config, you can construct an instance of the required config object and pass it in directly.

<CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-config.py" language="python" />

### Assets with resources \{#resources}

If an asset uses a resource, it can be useful to create a mock instance of the resource to avoid interacting with external services.

<CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-resource.py" language="python" />

### Assets with context \{#context}

If an asset uses a `context` argument, you can use `build_asset_context()` to construct a context object.

<CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-context.py" language="python" />

### Assets with multiple parameters \{#multiple-parameters}

If an asset has multiple parameters, we recommended using keyword arguments for clarity.

<CodeExample filePath="guides/quality-testing/unit-testing-assets-and-ops/asset-combo.py" language="python" />

## Running the tests

Use `pytest` or your test runner of choice to run your unit tests. Navigate to the top-level project directory (the one that contains the tests directory) and run:

```
pytest my_project_tests
```