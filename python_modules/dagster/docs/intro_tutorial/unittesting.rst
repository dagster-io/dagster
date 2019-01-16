Unit-testing Pipelines
----------------------

Unit testing data pipelines is, broadly speaking, quite difficult. As a result, it is typically
never done.

One of the mechanisms included in dagster to enable testing has already been discussed: contexts.
The other mechanism is the ability to execute arbitrary subsets of a DAG. (This capability is
useful for other use cases but we will focus on unit testing for now).

Let us start where we left off.

We have the following pipeline:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/unittesting.py
    :linenos:
    :caption: unittesting.py
    :lines: 1-45

Let's say we wanted to test *one* of these solids in isolation.

We want to do is isolate that solid and execute with inputs we
provide, instead of from solids upstream in the dependency graph.

So let's do that. Follow along in the comments:

.. literalinclude:: ../../dagster/tutorials/intro_tutorial/unittesting.py
    :linenos:
    :caption: unittesting.py
    :lines: 47-53

We can also execute entire arbitrary subdags rather than a single solid using
the ``execute_solids`` function


.. literalinclude:: ../../dagster/tutorials/intro_tutorial/unittesting.py
    :linenos:
    :caption: unittesting.py
    :lines: 55-63
