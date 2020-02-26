.. py:currentmodule:: dagster

Testing solids and pipelines
----------------------------

Our first solid and pipeline wouldn't be complete without some tests to ensure they're working as
expected. We'll use :py:func:`execute_pipeline` to test our pipeline, as well as
:py:func:`execute_solid` to test our solid in isolation.

These functions synchronously execute a pipeline or solid and return results objects (the
:py:class:`SolidExecutionResult` and :py:class:`PipelineExecutionResult`) whose methods let us
investigate, in detail, the success or failure of execution, the outputs produced by solids, and
(as we'll see later) other events associated with execution.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/hello_cereal.py
   :linenos:
   :caption: hello_cereal.py
   :lineno-start: 31
   :lines: 31-40
   :language: python

Now you can use pytest, or your test runner of choice, to run unit tests as you develop your
data applications.

.. code-block:: console

    $ pytest hello_cereal.py

Note: by convention, pytest tests are typically kept in separate files prefixed with ``test_``.
We've put them in the same file just to simplify the tutorial code.

Obviously, in production we'll often execute pipelines in a parallel, streaming way that doesn't
admit this kind of API, which is intended to enable local tests like this.

Dagster is written to make testing easy in a domain where it has historically been very difficult.
Throughout the rest of this tutorial, we'll explore the writing of unit tests for each piece of
the framework as we learn about it.
