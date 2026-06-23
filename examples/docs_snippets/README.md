# Docs snippets

This directory contains code referenced in Dagster docs.

This module exists only to enable testing docs snippets/examples in CI, and should not be installed
otherwise.

## Code style

Please use the following code style to keep imports short:

```python
import dagster as dg

@dg.asset
def my_cool_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    return dg.MaterializeResult(
        metadata={
            "foo": "bar",
        }
    )
```

## Testing

Snippet tests live in `docs_snippets_tests`.

### Prerequisites

Before running tests, you will need to create a virtual environment and run `make dev_install` in the root folder of the Dagster repo, then set the `DAGSTER_GIT_REPO_DIR` environment variable.

### Test all code loads into Python

From the `example/docs_snippets` directory (with your virtual environment active and `tox` available), you can test that all code loads into Python correctly with:

```
pip install tox-uv
tox
```

**Note:** To exclude a snippet file from the file load test, see [Exclude a snippet file from the file load test](#exclude-a-snippet-file-from-the-file-load-test).

### Run all tests

From the `example/docs_snippets` directory (with your virtual environment active and `tox` available), you can run all tests with:

```
tox -e all
```

This runs all documentation tests, which can be slow and result in a less-than-ideal feedback loop. See below for guidance on [testing specific files](#test-specific-files) or [running specific tests](#run-specific-tests).

### Test specific files

From the `example/docs_snippets` directory (with your virtual environment active and `tox` available), you can test specific files with:

```
TOX_TESTENV_PASSENV=PYTEST_ADDOPTS PYTEST_ADDOPTS="docs_snippets_tests/{PATH TO TEST}.py" tox -e all
```

### Run specific tests

From the `example/docs_snippets` directory (with your virtual environment active and `tox` available), you can run specific tests with:

```
TOX_TESTENV_PASSENV=PYTEST_ADDOPTS PYTEST_ADDOPTS="docs_snippets_tests/{PATH TO TEST}.py::{TEST NAME}" tox -e all
```

### Exclude a snippet file from the file load test

By default, whenever a file is added to `examples/docs_snippets/docs_snippets`, the `test_file_loads` test ensures that the file can be successfully loaded.

There are two variations of the `test_file_loads` test, covering both docs snippets and integrations:

- [docs_snippets_tests/test_integration_files_load.py](docs_snippets_tests/test_integration_files_load.py)
- [docs_snippets_tests/test_all_files_load.py](docs_snippets_tests/test_all_files_load.py)

If you need to exclude a file (typically due to relative imports or other import issues), add it to the `EXCLUDED_FILES` list at the top of the test.
