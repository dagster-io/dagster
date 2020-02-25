Conditional Execution/Branching
===============================

What are optional outputs?
--------------------------

An output can be marked as ``is_optional`` in an :class:`OutputDefinitions <dagster.OutputDefinition>`.
This means that the output does not necessarily have to be yielded by
the solid.

If an optional output is not yielded, all downstream solids that depend
on the output will simply skip, such as short-circuiting or branching.

For example:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/conditional_execution.py
   :linenos:
   :lines: 8-11
   :language: python

How do I conditionally branch in my pipeline?
---------------------------------------------

By taking advantage of optional outputs and skips, we can implement
branching in our pipeline.

For example, let’s define a solid that has two optional outputs, and
only yields one based on a conditional:


.. literalinclude:: ../../../../examples/dagster_examples/how_tos/conditional_execution.py
   :linenos:
   :lines: 14-24
   :language: python


Then, we can have two downstream solids ``path_1`` and ``path_2`` that
depend on output “a” and output “b”, respectively:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/conditional_execution.py
   :linenos:
   :lines: 27-34
   :language: python


Finally, we can wire these solids up in a pipeline:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/conditional_execution.py
   :linenos:
   :lines: 37-41
   :language: python


Depending on the value of the conditional, only ``path_1`` or ``path_2``
will execute.

How do I manage error handling in a solid?
------------------------------------------

There are two types of possible errors that can happen in the body of a
solid’s ``compute_fn``:

1. A python runtime exception that is unexpected
2. Running into a known exception or invalid state

*Case 1: Python runtime exception*

When an exception is thrown in a solid’s ``compute_fn``, the error is
caught by a user error boundary and surfaced in the event stream. Any
downstream solids that depend on the solid will be marked as skipped and
will not execute.

*Case 2: Known invalid state or unrecoverable failure*

If you run into a known failure state, you can ``raise`` a
:class:`Failure <dagster.Failure>` event from a solid to in order to notify the Dagster
executor of the failure as well as return structured metadata about the
failure.

For example, a scenario where you want to "fail successfully" is when you have an external data
store that is not ready/available.

Any downstream solids that depend on the solid will be marked as skipped and will not execute.

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/conditional_execution.py
   :linenos:
   :lines: 52-59
   :language: python
