# dbt with software-defined assets tutorial example

This example is meant to be used alongside the [Using dbt with Dagster software-defined assets tutorial](https://docs.dagster.io/integrations/dbt/using-dbt-with-dagster).

The tutorial associated with this example demonstrates how to integrate dbt with Dagster using dbt's example [jaffle shop project](https://github.com/dbt-labs/jaffle_shop), the [dagster-dbt library](/\_apidocs/libraries/dagster-dbt), and a [DuckDB database](https://duckdb.org/).

This example contains:

- A blank template project (located in `tutorial_template`) that can be used to follow along with the tutorial
- A finished project (`tutorial_finished`) that contains the completed project produced by the tutorial

---

## Getting started

To download this example, run:

```shell
dagster project from-example --name my-dagster-project --example tutorial_dbt_dagster
```

To install this example and its dependencies, run:

```shell
cd my-dagster-project
pip install -e ".[dev]"
```

At this point, you can view the **completed** project in Dagit by running:

```shell
cd tutorial_finished
dagit
```