.. py:currentmodule:: dagster

Hello, solid!
^^^^^^^^^^^^^

Let's write our first Dagster solid and save it as ``hello_cereal.py``.

(You can also find this file, and all of the tutorial code, on
`Github <https://github.com/dagster-io/dagster/tree/master/examples/dagster_examples/intro_tutorial>`__
or, if you've cloned the git repo, at ``dagster/examples/dagster_examples/intro_tutorial/``.)

A solid is a unit of computation in a data pipeline. Typically, you'll define solids by
annotating ordinary Python functions with the :py:func:`@solid <solid>` decorator.

The logic in our first solid is very straightforward: it just reads in the csv from a hardcoded path
and logs the number of rows it finds.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :lines: 1-18
   :caption: hello_cereal.py
   :language: python

In this simplest case, our solid takes no inputs except for the
:py:class:`context <SystemComputeExecutionContext>` in which it executes
(provided by the Dagster framework as the first argument to every solid), and also returns no
outputs. Don't worry, we'll soon encounter solids that are much more dynamic.
