Hello, DAG
----------
One of the core capabitilies of dagster is the ability to express data pipelines as arbitrary
directed acyclic graphs (DAGs) of solids.

Let's define a very simple two-solid pipeline whose first solid returns a hardcoded string,
and whose second solid concatenates two copies of its input. The output of the pipeline should be
two concatenated copies of the hardcoded string.

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/hello_dag.py
   :linenos:
   :caption: hello_dag.py

This pipeline introduces a few new concepts.

1.  Solids can have **inputs** defined by instances of
    :py:class:`InputDefinition <dagster.InputDefinition>`. Inputs allow us to connect solids to
    each other, and gives dagster information about solids' dependencies (and, as we'll see later,
    optionally let dagster check the types of the inputs at runtime).

2.  Solids' **dependencies** on each other are expressed by instances of 
    :py:class:`DependencyDefinition <dagster.DependencyDefinition>`.
    You'll notice the new argument to :py:class:`PipelineDefinition <dagster.PipelineDefinition>`
    called ``dependencies``, which is a dict that defines the connections between solids in a
    pipeline's DAG.

    .. literalinclude::  ../../dagster/tutorials/intro_tutorial/hello_dag.py
       :lines: 22-26
       :dedent: 8

    The first layer of keys in this dict are the *names* of solids in the pipeline. The second layer
    of keys are the *names* of the inputs to each solid. Each input in the DAG must be provided a
    :py:class:`DependencyDefinition <dagster.DependencyDefinition>`. (Don't worry -- if you forget
    to specify an input, a helpful error message will tell you what you missed.)
    
    In this case the dictionary encodes the fact that the input ``arg_one`` of solid ``solid_two``
    should flow from the output of ``solid_one``.

Let's visualize the DAG we've just defined in dagit.

.. code-block:: console

   $ dagit -f hello_dag.py -n define_hello_dag_pipeline

.. image:: hello_dag_fig_one.png

One of the distinguishing features of dagster that separates it from many workflow engines is that
dependencies connect *inputs* and *outputs* rather than just *tasks*. An author of a dagster
pipeline defines the flow of execution by defining the flow of *data* within that
execution. This is core to the the programming model of dagster, where each step in the pipeline
-- the solid -- is a *functional* unit of computation. 

Now run the pipeline we've just defined, either from dagit or from the command line:

.. code-block:: console

	$ dagster pipeline execute -f hello_dag.py -n define_hello_dag_pipeline

In the next section, :doc:`An actual DAG <actual_dag>`, we'll build our first DAG with interesting
topology and see how dagster determines the execution order of a pipeline.
