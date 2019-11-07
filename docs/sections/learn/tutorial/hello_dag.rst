.. py:currentmodule:: dagster

Connecting solids together
--------------------------

Our pipelines wouldn't be very interesting if they were limited to solids acting in isolation
from each other. Pipelines are useful because they let us connect solids into arbitrary DAGs
(`directed acyclic graphs <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_) of computation.


Let's get serial
^^^^^^^^^^^^^^^^

We'll add a second solid to the pipeline we worked with in the first section of the tutorial.

This new solid will consume the output of the first solid, which read the cereal dataset in from
disk, and in turn will sort the list of cereals by their calorie content per serving.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/serial_pipeline.py
   :linenos:
   :lines: 1-37
   :emphasize-lines: 15, 19, 37
   :caption: serial_pipeline.py

You'll see that we've modified our existing ``load_cereals`` solid to return an output, in this
case the list of dicts into which :py:class:``csv.DictReader <python:csv.DictReader>`` reads the
cereals dataset.

We've defined our new solid, ``sort_by_calories``, to take a user-defined input, ``cereals``, in
addition to the system-provided :py:class:`context <SystemComputeExecutionContext>` object.

We can use inputs and outputs to connect solids to each other. Here we tell Dagster that
although ``load_cereals`` doesn't depend on the output of any other solid, ``sort_by_calories``
does -- it depends on the output of ``load_cereals``.

Let's visualize the DAG we've just defined in dagit.

.. code-block:: console

   $ dagit -f serial_pipeline.py -n serial_pipeline

Navigate to http://127.0.0.1:3000/p/serial_pipeline/explore or choose "serial_pipeline"
from the dropdown:

.. thumbnail:: serial_pipeline_figure_one.png

A more complex DAG
^^^^^^^^^^^^^^^^^^

Solids don't need to be wired together serially. The output of one solid can be consumed by any
number of other solids, and the outputs of several different solids can be consumed by a single
solid.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/complex_pipeline.py
   :linenos:
   :lines: 6-64
   :lineno-start: 6
   :emphasize-lines: 55-59
   :caption: complex_pipeline.py

First we introduce the intermediate variable ``cereals`` into our pipeline definition to
represent the output of the ``load_cereals`` solid. Then we make both ``sort_by_calories`` and
``sort_by_protein`` consume this output. Their outputs are in turn both consumed by
``display_results``.

Let's visualize this pipeline in Dagit (``dagit -f complex_pipeline.py -n complex_pipeline``):

.. thumbnail:: complex_pipeline_figure_one.png

When you execute this example from Dagit, you'll see that ``load_cereals`` executes first,
followed by ``sort_by_calories`` and ``sort_by_protein`` -- in any order -- and that
``display_results`` executes last, only after ``sort_by_calories`` and ``sort_by_protein`` have
both executed.

In more sophisticated execution environments, ``sort_by_calories`` and ``sort_by_protein`` could
execute not just in any order, but at the same time, since they don't depend on each other's
outputs -- but both would still have to execute after ``load_cereals`` (because they depend on its
output) and before ``display_results`` (because ``display_results`` depends on both of
their outputs).

We'll write a simple test for this pipeline showing how we can assert that all four of its solids
executed successfully.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/test_complex_pipeline.py
   :linenos:
   :lines: 6-11
   :lineno-start: 6
   :caption: test_complex_pipeline.py
