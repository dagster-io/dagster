---
title: "dagstermill integration reference"
description: The Dagstermill package lets you run notebooks using the Dagster tools and integrate them into your data pipelines.
sidebar_position: 200
---

This reference provides a high-level look at working with Jupyter notebooks using the [`dagstermill` integration library](/api/python-api/libraries/dagstermill).

For a step-by-step implementation walkthrough, refer to the [Using notebooks with Dagster tutorial](using-notebooks-with-dagster).

## Notebooks as assets

To load a Jupyter notebook as a Dagster [asset](/guides/build/assets/defining-assets), use <PyObject section="libraries" module="dagstermill" object="define_dagstermill_asset" />:

<CodeExample path="docs_snippets/docs_snippets/integrations/dagstermill/iris_notebook_asset.py" />

In this code block, we use `define_dagstermill_asset` to create a Dagster asset. We provide the name for the asset with the `name` parameter and the path to our `.ipynb` file with the `notebook_path` parameter. The resulting asset will execute our notebook and store the resulting `.ipynb` file in a persistent location.

## Notebooks as ops

Dagstermill also supports running Jupyter notebooks as [ops](/guides/build/ops). We can use <PyObject section="libraries" module="dagstermill" object="define_dagstermill_op" /> to turn a notebook into an op:

<CodeExample path="docs_snippets/docs_snippets/integrations/dagstermill/iris_notebook_op.py" startAfter="start" />

In this code block, we use `define_dagstermill_op` to create an op that will execute the Jupyter notebook. We give the op the name `k_means_iris`, and provide the path to the notebook file. We also specify `output_notebook_name=iris_kmeans_output`. This means that the executed notebook will be returned in a buffered file object as one of the outputs of the op, and that output will have the name `iris_kmeans_output`. We then include the `k_means_iris` op in the `iris_classify` [job](/guides/build/jobs) and specify the `ConfigurableLocalOutputNotebookIOManager` as the `output_notebook_io_manager` to store the executed notebook file.

## Notebook context

If you look at one of the notebooks executed by Dagster, you'll notice that the `injected-parameters` cell in your output notebooks defines a variable called `context`. This context object mirrors the execution context object that's available in the body of any other asset or op's compute function.

As with the parameters that `dagstermill` injects, you can also construct a context object for interactive exploration and development by using the `dagstermill.get_context` API in the tagged `parameters` cell of your input notebook. When Dagster executes your notebook, this development context will be replaced with the injected runtime context.

You can use the development context to access asset and op config and resources, to log messages, and to yield results and other Dagster events just as you would in production. When the runtime context is injected by Dagster, none of your other code needs to change.

For instance, suppose we want to make the number of clusters (the _k_ in k-means) configurable. We'll change our asset definition to include a config field:

<CodeExample path="docs_snippets/docs_snippets/integrations/dagstermill/iris_notebook_config.py" startAfter="start" endBefore="end" />

You can also provide `config_schema` to `define_dagstermill_op` in the same way demonstrated in this code snippet.

In our notebook, we'll stub the context as follows (in the `parameters` cell):

```python
import dagstermill

context = dagstermill.get_context(op_config=3)
```

Now we can use our config value in our estimator. In production, this will be replaced by the config value provided to the job:

```python
estimator = sklearn.cluster.KMeans(n_clusters=context.op_config)
```

## Results and custom materializations

:::note

The functionality described in this section only works for notebooks run with `define_dagstermill_op`. If you'd like adding this feature to `define_dagstermill_asset` to be prioritized, give this [GitHub issue](https://github.com/dagster-io/dagster/issues/10557) a thumbs up.

:::

If you are using `define_dagstermill_op` and you'd like to yield a result to be consumed downstream of a notebook, you can call <PyObject section="libraries" module="dagstermill" object="yield_result" /> with the value of the result and its name. In interactive execution, this is a no-op, so you don't need to change anything when moving from interactive exploration and development to production.


<CodeExample path="docs_snippets/docs_snippets/integrations/dagstermill/notebook_outputs.py" startAfter="start_notebook" endBefore="end_notebook" />

And then:

<CodeExample path="docs_snippets/docs_snippets/integrations/dagstermill/notebook_outputs.py" startAfter="start_py_file" endBefore="end_py_file" />

## Dagster events

You can also yield Dagster events from your notebook using <PyObject section="libraries" module="dagstermill" object="yield_event" />.

For example, if you'd like to yield a custom <PyObject section="ops" module="dagster" object="AssetMaterialization" /> object (for instance, to tell the Dagster UI where you've saved a plot), you can do the following:

```python
import dagstermill
from dagster import AssetMaterialization

dagstermill.yield_event(AssetMaterialization(asset_key="marketing_data_plotted"))
```
