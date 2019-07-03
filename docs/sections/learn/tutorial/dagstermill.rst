============
Dagstermill
============

A wonderful feature of using Dagster is that you can productionize Jupyter notebooks and involve
them in a (production) pipeline as units of computation.

There are a few stages of data scientists using notebooks in the wild.

1. Unstructured scratch work, cells are often run out of order.
2. More refined prototyping, where cells are run sequentially. Usually the top cells contain
   parameters that are used in later cells.
3. Pieces of re-usable code are extracted from a notebook, turned into functions and put in a
   script (``.py`` file)

Typically, only stage 3 would be involved in a production pipeline. However, with dagstermill, if
you have a notebook in stage 2 (i.e. cells run sequentially to produce the desired output), with
minimal effort you can register this notebook as a solid in the pipeline and use the notebook driven
solid as a unit of computation that takes in inputs and produces outputs (that can be consumed by
later stages of the pipeline).

------------------------------------------
A (Very Simple) Pipeline with a Notebook
------------------------------------------

Say you have a pipeline as shown below:

.. image:: test_add_pipeline.png

This is a very simple pipeline, where the solid ``return_one`` returns 1 and ``return_two`` returns
2. The notebook driven solid ``add_two_numbers`` simply adds two numbers and returns the result,
as the name suggests.

The notebook might have a cell that looks like the following:

.. code-block:: python

    a = 3
    b = 5
    result = 3 + 5

Currently your notebook simply adds together the numbers ``3`` and ``5``, but in a more generic
sense, your notebook is effectively a function that takes in inputs ``a`` and ``b`` and products
output ``result``. To use the language of the dagster abstraction, it is a solid with inputs
``a``, ``b`` of dagster-type ``Int`` and with an output ``result`` of type ``Int``.

To register this notebook as a dagster solid, we use the following lines of code.

.. code-block:: python

    from dagster import InputDefinition, OutputDefinition, Int
    from dagstermill import define_dagstermill_solid

    my_notebook_solid = define_dagstermill_solid(
        name='add_two_numbers',
        notebook_path='/notebook/path/add_two_numbers.ipynb',
        input_defs = [
            InputDefinition(name='a', dagster_type=Int),
            InputDefinition(name='b', dagster_type=Int)
        ],
        output_defs = [OutputDefinition(Int)]
    )

The function ``dm.define_dagstermill_solid()`` returns an object of type ``SolidDefinition`` that
can be passed into ``PipelineDefinition`` objects. We see that its arguments are rather
self-explanatory:

* ``name``: the name of the solid
* ``notebook_path``: the location of the notebook so that the dagster execution engine can run the
  code in the notebook
* ``inputs``, ``outputs``: the named and typed inputs and outputs of the notebook as a solid

Typically, you'll want to be able to execute the notebook interactively as well as through
dagstermill. In this case, you'll put any shim values for the inputs that will be provided in
production by dagstermill into a special notebook cell tagged ``parameters``:

..image:: add_two_numbers.png

This cell will be replaced by injected inputs when the notebook is run through dagstermill.

If the notebook-driven solid has an output, you'll also want to call ``dagstermill.yield_result()``
inside the notebook in order to yield the result back to Dagster. In interactive execution, this is
a no-op.

----------------------------------------
Output Notebooks & How Dagstermill Works
----------------------------------------

The way dagstermill works is by auto-injecting a cell that replaces the `parameters`-tagged cell
with the runtime values of the inputs and then running the notebook using the
`papermill <https://github.com/nteract/papermill/>`_ library. A nice side effect of using the
papermill library to run the notebook is that the output is contained in an "output notebook",
and the source notebook remains unchanged. Since the output notebook is itself a valid Jupyter
notebook, debugging can be done within the notebook environment!

The execution log contains the path to the output notebook so that you can access it after
execution to examine and potentially debug the output. Within dagit we also provide a link to
the output notebook, as shown below.

.. image:: output_notebook.png
