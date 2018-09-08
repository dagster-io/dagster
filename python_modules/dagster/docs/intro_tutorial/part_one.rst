Hello, World
------------

The first step is to get dagster up and running quickly. We will initially be using the
python API for executing pipelines and eventually move on to driving execution and
inspecting pipelines with tools.


    .. code-block:: python

        # Do not recommend using wildcard imports in production code
        from dagster import * 

        @lambda_solid
        def hello_world():
            print('hello')

        if __name__ == '__main__':
            execute_pipeline(PipelineDefinition(solids=[hello_world]))

This example introduces three concepts:

1) A solid. ``@lambda_solid`` marks the the function ``hello_world`` as solid. A solid represents
a functional unit of computations in a data pipeline. A lambda is a minimal form of a solid. We
will explore more aspects of solids as this tutorial continues.

2) A pipeline. The call to ``PipelineDefinition`` which a set of solids arranged to do a
computation that produces data assets. In this case we are creating a pipeline with a single
solid and nothing else.

3) ``execute_pipeline``. This will execute the pipeline. The framework will eventually call back
into ``hello_world`` and print hello to the screen.

Save this to a file called ``step_one.py`` and run

.. code-block:: sh

    $ python3 step_one.py
    hello

Congrats! You have run your first pipeline.