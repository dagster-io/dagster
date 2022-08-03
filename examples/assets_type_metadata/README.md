## Using Dagster with Types and Metadata Example

The example builds a small graph of software-defined assets that compute bollinger bands for S&P 500 prices.

### Features demonstrated

- Software-defined assets.
- Dagster types.
- `dagster-pandera` integration.
- Custom `IOManager`.
- Definition-level metadata on assets.

## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example assets_type_metadata
```

To install this example and its Python dependencies, run:

```bash
pip install -e .
```

Once you've done this, you can run:

```
dagit
```

to view this example in Dagster's UI, Dagit.