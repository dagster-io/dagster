Unit-testing Pipelines
----------------------

Historically in production data engineering systems, unit testing data pipelines is quite difficult
to implement. As a result, it is frequently omitted from data engineering workflows, and pipelines
are instead tested end-to-end in a dev environment.

One of the mechanisms included in dagster to enable testing has already been discussed: the
:doc:`Execution Context <execution_context>`. Recall that the context allows us to configure the
pipeline-level execution environment while keeping all of the code in our pipelines unchanged.

The other important testing mechanism is the ability to execute arbitrary subsets of a DAG. (This
capability is useful for other use cases but we will focus on unit testing for now).

Let's start where we left off.

We have the following pipeline:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/unittesting.py
    :linenos:
    :caption: unittesting.py
    :lines: 1-45

Let's say we wanted to test *one* of these solids in isolation.

We want to do is isolate that solid and execute with inputs we
provide, instead of from solids upstream in the dependency graph.

So let's do that. Follow along in the comments:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/unittesting.py
    :linenos:
    :caption: unittesting.py
    :lines: 47-53

We can also execute entire arbitrary subdags rather than a single solid using
the ``execute_solids`` function


.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/unittesting.py
    :linenos:
    :caption: unittesting.py
    :lines: 55-63
