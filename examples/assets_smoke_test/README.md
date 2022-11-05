# Data Pipeline Smoke Test Example

This example demonstrates how to write a smoke test that exercises all the transformations in a data pipeline.

It contains two separate asset graphs:
- assets_smoke_test/pure_python_assets.py contains an asset graph implemented entirely in Python.
- assets_smoke_test/python_and_dbt_assets.py contains an asset graph implemented both in Python and dbt.

Each has its own smoke test, in the assets_smoke_test_tests directory.

## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example assets_smoke_test
```

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```
