Hello, World
------------
See :doc:`../installation` for instructions getting dagster -- the core library -- and dagit -- the 
the web UI tool used to visualize your data pipelines -- installed on your platform of choice.

Let's write our first pipeline:

.. literalinclude:: ../../tutorials/intro_tutorial/part_one.py
   :linenos:
   :caption: part_one.py

This example introduces three concepts:

1) A **solid** is a functional unit of computation in a data pipeline. In this example, we use the
decorator ``@lambda_solid`` to mark the function ``hello_world`` as a solid: a functional unit
which takes no inputs and returns the output ``'hello'`` every time it's run.

2) A **pipeline** is a set of solids arranged into a DAG of computation that produces data assets.
In this example, the call to ``PipelineDefinition`` defines a pipeline with a single solid.

3) We **execute** the pipeline by running ``execute_pipeline``. Dagster will call into each solid
in the pipeline, functionally transforming its inputs, if any, and threading its outputs to solids
further on in thre DAG.

Save this to a file called ``part_one.py``, and let's use dagit to visualize and execute it.

.. code-block:: sh

   dagit -f step_one.py -n define_pipeline

And send your web browser to http://localhost:3000/ and you can view your pipeline.

In order to execute this pipeline we can use the dagster CLI tool:

.. code-block:: sh

    $ dagster pipeline execute -f step_one.py -n define_pipeline
    hello
    2018-09-18 08:48:50 - dagster - INFO - orig_message="Solid hello_world emitted output \"result\" value None" log_message_id="d315f5f2-4f36-443b-b225-05cd31e6f10c" solid="hello_world"

Note the logs that indicate that this actually execute something.

This can also be fixed using an in-memory python API. Add this to end of your file
(as well as adding ``execute_pipeline`` to your include list):

.. code-block:: python

    if __name__ == '__main__':
        result = execute_pipeline(define_pipeline())
        assert result.success

Assuming the file is saved as ``step_one.py``:

.. code-block:: sh

    $ python3 step_one.py
    hello

And now you have run your first pipeline in using both the CLI and the python API.