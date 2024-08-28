# Docs Beta Examples

This module exists only to enable testing docs snippets/examples in CI, and should not be installed
otherwise.

## Code Style

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

You may include additional test files in `docs_beta_snippets_tests`
