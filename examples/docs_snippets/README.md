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
