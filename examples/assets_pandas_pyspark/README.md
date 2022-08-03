# Software-Defined Assets with Pandas and PySpark Example

In this example, we'll define some tables with dependencies on each other. We have a table of temperature samples collected in five-minute increments, and we want to compute a table of the highest temperatures for each day.

View this example in the Dagster docs at [Software-Defined Assets with Pandas and PySpark](https://docs.dagster.io/guides/dagster/software-defined-assets).


## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example assets_pandas_pyspark
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