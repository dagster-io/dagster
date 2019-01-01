Hello, World
------------
See :doc:`../installation` for instructions getting dagster -- the core library -- and dagit --  
the web UI tool used to visualize your data pipelines -- installed on your platform of choice.

Let's write our first pipeline and save it as ``hello_world.py``.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/hello_world.py
   :linenos:
   :lines: 1-2, 4-17
   :caption: hello_world.py

This example introduces three concepts:

1.  A **solid** is a functional unit of computation in a data pipeline. In this example, we use the
    decorator :py:func:`@lambda_solid <dagster.lambda_solid>` to mark the function ``hello_world``
    as a solid: a functional unit which takes no inputs and returns the output ``'hello'`` every
    time it's run.

2.  A **pipeline** is a set of solids arranged into a DAG of computation that produces data assets.
    In this example, the call to :py:class:`PipelineDefinition <dagster.PipelineDefinition>` defines
    a pipeline with a single solid.

3.  We **execute** the pipeline by running :py:func:`execute_pipeline <dagster.execute_pipeline>`.
    Dagster will call into each solid in the pipeline, functionally transforming its inputs, if any,
    and threading its outputs to solids further on in thre DAG.

Pipeline Execution
^^^^^^^^^^^^^^^^^^

Assuming you've saved this pipeline as ``hello_world.py``, we can execute it via three different mechanisms:

1. The CLI utility `dagster`
2. The GUI tool `dagit`
3. Using dagster as a library within your own script.

CLI
~~~

.. code-block:: console

    $ dagster pipeline execute -f hello_world.py -n define_hello_world_pipeline

There's a lot of information in these log lines (we'll get to how you can use, and customize,
them later), but you can see that the third message is:
```Solid hello_world emitted output \"result\" value 'hello'"```. Success!

Dagit
~~~~~

To visualize your pipeline (which only has one node) in dagit, you can run:

.. code-block:: console

   $ dagit -f hello_world.py -n define_hello_world_pipeline
   Serving on http://127.0.0.1:3000

You should be able to navigate to http://127.0.0.1:3000/hello_world_pipeline/explore in your web
browser and view your pipeline.

.. image:: hello_world_fig_one.png

There are lots of ways to execute dagster pipelines. If you navigate to the "Execute"
tab (http://127.0.0.1:3000/hello_world_pipeline/execute), you can execute your pipeline directly from
dagit. Logs will stream into the bottom right pane of the interface, where you can filter them by
log level.

.. image:: hello_world_fig_two.png

Library
~~~~~~~

If you'd rather execute your pipelines as a script, you can do that without using the dagster CLI
at all. Just add a few lines to `hello_world.py` (highlighted in yellow):

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/hello_world.py
   :linenos:
   :caption: hello_world.py
   :emphasize-lines: 3,19-21

Then you can just run:

.. code-block:: console

    $ python hello_world.py

Next, let's build our first multi-solid DAG in :doc:`Hello, DAG <part_two>`!
