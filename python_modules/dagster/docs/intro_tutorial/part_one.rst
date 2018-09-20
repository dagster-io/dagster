Hello, World
------------

The first step is to get dagster up and running quickly. Let's first install dagster -- the core
library -- and dagit -- the web UI tool used to visualize your data pipelines.

.. code-block:: sh

    $ pip install dagster
    $ pip install dagit

Now let's write our first pipeline:

    .. code-block:: python

        from dagster import (
            PipelineDefinition,
            execute_pipeline,
            lambda_solid,
        )

        @lambda_solid
        def hello_world():
            print('hello')

        def define_pipeline():
            return PipelineDefinition(
                name='hello_world_pipeline',
                solids=[hello_world],
            )

This example introduces three concepts:

1) A **solid**. ``@lambda_solid`` marks the the function ``hello_world`` as solid. A solid represents
a functional unit of computation in a data pipeline. A lambda is a minimal form of a solid. We
will explore more aspects of solids as this tutorial continues.

2) A **pipeline**. The call to ``PipelineDefinition`` which a set of solids arranged to do a
computation that produces data assets. In this case we are creating a pipeline with a single
solid and nothing else.

3) ``execute_pipeline``. This will execute the pipeline. Dagster will execute the pipeline and
eventually call back into ``hello_world`` and print to the screen.

Save this to a file called ``step_one.py`` and can visualize it and execute it.

.. code-block:: sh

   dagit -f step_one.py -r define_pipeline

And send your web browser to http://localhost:3000/ and you can view your pipeline.

In order to execute this pipeline we can use the dagster CLI tool:

.. code-block:: sh

    $ dagster pipeline execute -f step_one.py -r define_pipeline
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