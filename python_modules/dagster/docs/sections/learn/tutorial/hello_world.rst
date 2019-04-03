Hello, World
------------
See :doc:`../../install/install` for instructions installing dagster (the core library) and dagit (the
web UI tool used to visualize your data pipelines) on your platform of choice.

Let's write our first pipeline and save it as ``hello_world.py``.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/hello_world.py
   :linenos:
   :lines: 1-12
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
    and threading its outputs to solids further on in the DAG.

Pipeline Execution
^^^^^^^^^^^^^^^^^^

Assuming you've saved this pipeline as ``hello_world.py``, we can execute it via any of three
different mechanisms:

1. The CLI utility `dagster`
2. The GUI tool `dagit`
3. Using dagster as a library within your own script.

CLI
~~~

.. code-block:: console

    $ dagster pipeline execute -f hello_world.py -n define_hello_world_pipeline
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Beginning execution of pipeline hello_world_pipeline" log_message_id="5c829421-06c7-49eb-9195-7e828e37eab8" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" event_type="PIPELINE_START"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Beginning execution of hello_world.transform" log_message_id="5878513a-b510-4837-88cb-f77205931abb" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" solid="hello_world" solid_definition="hello_world" event_type="EXECUTION_PLAN_STEP_START" step_key="hello_world.transform"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Solid hello_world emitted output \"result\" value 'hello'" log_message_id="b27fb70a-744a-46cc-81ba-677247b1b07b" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" solid="hello_world" solid_definition="hello_world"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Execution of hello_world.transform succeeded in 0.9558200836181641" log_message_id="25faadf5-b5a8-4251-b85c-dea6d00d99f0" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" solid="hello_world" solid_definition="hello_world" event_type="EXECUTION_PLAN_STEP_SUCCESS" millis=0.9558200836181641 step_key="hello_world.transform"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Step hello_world.transform emitted 'hello' for output result" log_message_id="604dc47c-fe29-4d71-a531-97ae58fda0f4" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline"
    2019-01-08 11:23:57 - dagster - INFO - orig_message="Completing successful execution of pipeline hello_world_pipeline" log_message_id="1563854b-758f-4ae2-8399-cb75946b0055" run_id="dfc8165a-f37e-43f5-a801-b602e4409f74" pipeline="hello_world_pipeline" event_type="PIPELINE_SUCCESS"

There's a lot of information in these log lines (we'll get to how you can use, and customize,
them later), but you can see that the third message is:
``Solid hello_world emitted output \"result\" value 'hello'``. Success!

Dagit
~~~~~

To visualize your pipeline (which only has one node) in dagit, you can run:

.. code-block:: console

   $ dagit -f hello_world.py -n define_hello_world_pipeline
   Serving on http://127.0.0.1:3000

You should be able to navigate to http://127.0.0.1:3000/hello_world_pipeline/explore in your web
browser and view your pipeline.

.. image:: hello_world_figure_one.png

There are lots of ways to execute dagster pipelines. If you navigate to the "Execute"
tab (http://127.0.0.1:3000/hello_world_pipeline/execute), you can execute your pipeline directly
from dagit. Logs will stream into the bottom right pane of the interface, where you can filter them
by log level.

.. image:: hello_world_figure_two.png

Library
~~~~~~~

If you'd rather execute your pipelines as a script, you can do that without using the dagster CLI
at all. Just add a few lines to `hello_world.py` (highlighted in yellow):

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/hello_world.py
   :linenos:
   :caption: hello_world.py
   :emphasize-lines: 15-17

Then you can just run:

.. code-block:: console

    $ python hello_world.py

Next, let's build our first multi-solid DAG in :doc:`Hello, DAG <hello_dag>`!
