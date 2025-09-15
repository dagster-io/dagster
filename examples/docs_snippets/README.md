# Docs snippets

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

You can test that all code loads into Python correctly with:

```
pip install tox-uv
tox
```

Note that before running tests, you will need to create a virtual environment and run `make dev_install` in the root folder of the Dagster repo, then set the `DAGSTER_GIT_REPO_DIR` environment variable.

You may include additional test files in `docs_snippets_tests`.

### Running Tests

From the `example/docs_snippets` directory (with your virtual environment active and `tox` available), you can run all tests with:

```
tox -e all
```

This runs all documentation tests, which can be slow and result in a less-than-ideal feedback loop. To run tests for a specific file:

### Testing Specific Files
```
TOX_TESTENV_PASSENV=PYTEST_ADDOPTS PYTEST_ADDOPTS="docs_snippets_tests/{PATH TO TEST}.py" tox -e all
```

### Testing Specific Tests
```
TOX_TESTENV_PASSENV=PYTEST_ADDOPTS PYTEST_ADDOPTS="docs_snippets_tests/{PATH TO TEST}.py::{TEST NAME}" tox -e all
```

### Test File Loads

By default, whenever a file is added to `examples/docs_snippets/docs_snippets`, the `test_file_loads` test ensures that the file can be successfully loaded.

There are two variations of the `test_file_loads` test, covering both docs snippets and integrations:

* [examples/docs_snippets/docs_snippets_tests/test_integration_files_load.py](examples/docs_snippets/docs_snippets_tests/test_integration_files_load.py)
* [examples/docs_snippets/docs_snippets_tests/test_all_files_load.py](examples/docs_snippets/docs_snippets_tests/test_all_files_load.py)

If you need to exclude a file (typically due to relative imports or other import issues), add it to the `EXCLUDED_FILES` list at the top of the test.
