Hello, DAG
----------

One of the core capabitilies of dagster is the ability to arrange solids into directed, acyclic
graphs (DAG) within pipelines. We will demonstrate how to do that.

We will be building a very simple pipeline where the first step returns a hardcoded string, then
passes that value to the next solid, which concatenates it to itself, and prints it.


    .. code-block:: python

        from dagster import * 

        @lambda_solid
        def solid_one():
            return 'foo'


        @lambda_solid(inputs=[InputDefinition('arg_one')])
        def solid_two(arg_one):
            print(arg_one * 2)


        if __name__ == '__main__':
            pipeline = PipelineDefinition(
                solids=[solid_one, solid_two],
                dependencies={
                    'solid_two': {
                        'arg_one': DependencyDefinition('solid_one'),
                    },
                }
            )
            pipeline_result = execute_pipeline(pipeline)

We have a couple new concepts here.

1) ``InputDefinition``: Creating an instance declares that a solid has an input. Dagster is
now aware of this input and can perform tasks like manage it dependencies.

2) ``DependencyDefinition``: You'll notice a new argument to ``PipelineDefinition`` called
``dependencies``. This defines the depenedency graph of the DAG resident within a pipeline.
The first layer of keys are the names of solids. The second layer of keys are the names of
the inputs to that particular solid. Each input in the DAG must be provided a
``DependencyDefinition``. In this case the dictionary encodes the fact that the input ``arg_one``
of solid ``solid_two`` should flow from the output of ``solid_one``.

One of the distinguishing features of dagster that separates it from many workflow engines is that
dependencies connect *inputs* and *outputs* rather than just *tasks*. An author of a dagster
pipeline defines the flow of execution, and also the flow of *data* within that
execution. Understanding this is critical to understanding the programming model of dagster, where
each step in the pipeline -- the solid -- is a *functional* unit of computation. 

Save this file to ``step_two.py``

and run

.. code-block:: sh

    $ python3 step_two.py
    foofoo