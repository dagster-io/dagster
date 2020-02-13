.. py:currentmodule:: dagster

Hello, pipeline!
^^^^^^^^^^^^^^^^

To execute our solid, we'll embed it in an equally simple pipeline.

A pipeline is a set of solids arranged into a DAG (or
`directed acyclic graph <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_) of computation.
You'll typically define pipelines by annotating ordinary Python functions with the
:py:func:`@pipeline <pipeline>` decorator.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :lineno-start: 21
   :lines: 21-23
   :caption: hello_cereal.py


Here you'll see that we call ``hello_cereal()``. This call doesn't actually execute the solid
-- within the body of functions decorated with :py:func:`@pipeline <pipeline>`, we use
function calls to indicate the dependency structure of the solids making up the pipeline. Here,
we indicate that the execution of ``hello_cereal`` doesn't depend on any other solids by calling
it with no arguments.
