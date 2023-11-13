# Dagster + Jupyter/Papermill [UNMAINTAINED]

This example is meant to be used alongside the [Using Jupyter notebooks with Papermill and Dagster tutorial](https://docs.dagster.io/integrations/dagstermill/using-notebooks-with-dagster).

The tutorial demonstrates how to run Jupyter notebooks using Dagster and integrate your Jupyter notebooks with the rest of your Dagster assets.

This example contains:

- A blank template project (located in `tutorial_template`) that can be used to follow along with the tutorial
- A finished project (`tutorial_finished`) that contains the completed project produced by the tutorial


---

## Getting started

To download this example, run:

```shell
dagster project from-example --name my-dagster-project --example tutorial_notebook_assets
```

To install this example and its dependencies, run:

```shell
cd my-dagster-project
pip install -e ".[dev]"
```

At this point, you can open the Dagster UI and see the finished tutorial. As you work through the tutorial, the template will be filled in and become viewable in the UI.

```shell
dagster dev
```
