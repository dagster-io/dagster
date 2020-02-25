Solids
================

What is a solid?
----------------

A solid is a functional unit of computation. It has defined inputs and
outputs, and multiple solids can be wired together to form a
:class:`Pipeline <dagster.PipelineDefinition>` by defining dependencies between solid inputs and outputs.

There are two ways to define a solid:

1. Wrap a python function in the :func:`@solid <dagster.solid>` decorator *[Preferred]*
2. Construct a :class:`SolidDefinition <dagster.SolidDefinition>` object

*Method 1: Using the decorator*

To use the :func:`@solid <dagster.solid>` decorator, wrap a function that takes a
``context`` argument as the first parameter. The context is provides
access to system information such as resources and solid configuration.
See `What is a solid context <#what-is-solid-context>`_ for more
information.


.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 6-8
   :language: python


*Method 2: Constructing the SolidDefinition object*

To construct a :class:`SolidDefinition <dagster.SolidDefinition>` object, you need to pass the
constructor a solid name, input definitions, output definitions, and a
``compute_fn``. The compute function is the same as the function you would decorate using the
:func:`@solid <dagster.solid>` decorator.

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 11-17
   :language: python


What is solid context?
----------------------

A context object is passed as the first parameter to a solid’s
``compute_fn``. The context is an instance of
:class:`SystemComputeExecutionContext <dagster.SystemComputeExecutionContext>`, and provides access to:

-  solid configuration (``context.solid_config``)
-  loggers (``context.log``)
-  resources (``context.resources``)
-  run ID (``context.run_id``)

For example, to access the logger

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 20-22
   :language: python



How do I define inputs and outputs for a solid?
-----------------------------------------------

Dependencies between solids in Dagster are defined using :class:`InputDefinitions <dagster.InputDefinition>` and
:class:`OutputDefinitions <dagster.OutputDefinition>`.

Input and Output definitions are:

-  Named
-  Optionally typed
-  Optionally have human readable descriptions

*Inputs:*

Inputs are arguments to a solid’s ``compute_fn``, and are specified
using :class:`InputDefinitions <dagster.InputDefinition>`. They can be passed from outputs of other
solids, or stubbed using config.

A solid only executes once all of its inputs have been resolved, which
means that the all of the outputs that the solid depends on have been
successfully yielded.

The argument names of the ``compute_fn`` must match the :class:`InputDefinitions <dagster.InputDefinition>`
names, and must be in the same order after the
context argument.

For example, if we wanted a solid with two inputs of type ``int``:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 25-27
   :language: python



*Outputs:*

Outputs are yielded from a solid’s ``compute_fn``. A solid can yield
multiple outputs.


.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 30-36
   :language: python



Using typehints to automatically infer ``InputDefinitions`` and ``OutputDefinitions``
-------------------------------------------------------------------------------------

If you are using python typehints, Dagster can automatically infer
:class:`InputDefinitions <dagster.InputDefinition>` and :class:`OutputDefinitions <dagster.OutputDefinition>`.

The restriction is that you can only use return type hints when
returning one output. This is because Dagster solids ``yield`` one or
more :class:`Outputs <dagster.Output>`, among other events, and returning a single value is
equivalent to yielding one output.

If you need to return *multiple* outputs from a solid, you still need to
explicitly define :class:`OutputDefinitions <dagster.OutputDefinition>`.

For example, the following are equivalent:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 39-49
   :language: python


What does a solid return?
-------------------------

A solid can yield a stream of events within its ``compute_fn`` to
communicate with the Dagster framework. These events must be one of the
following types:

-  :class:`Output <dagster.Output>`
-  :class:`Materialization <dagster.Materialization>`
-  :class:`ExpectationResult <dagster.ExpectationResult>`
-  :class:`TypeCheck <dagster.TypeCheck>`
-  :class:`Failure <dagster.Failure>` (meant to be raised)


To return an output from a solid, simply ``yield`` an :class:`Output <dagster.Output>` event:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 52-54
   :language: python



Many solids yield only one output, like the example above. Returning a
single value from a solid’s ``compute_fn`` is equivalent to yielding a
single :class:`Outputs <dagster.Output>` event with the default output name “result”. For
example:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 57-65
   :language: python


Note that you cannot ``yield`` a single value without wrapping it
:class:`Outputs <dagster.Output>`. This is because a solid can yield arbitrarily many
values, and there’s no way for the system to tell which one the author
of the solid meant to use as its output. For example:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 68-71
   :language: python

If you want to have multiple outputs for a solid, you cannot return
anything from the solid. Instead, you need to ``yield`` multiple
:class:`Outputs <dagster.Output>` events, each of which is named and defined on ``output_defs``
to prevent ambiguity:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 74-77
   :language: python


Programmatically generating solids (Solid factories):
-----------------------------------------------------

You may find the need to create utilities that help generate solids.

Generally, you want to parameterize solid behavior by adding solid
configuration. You should reach for this pattern if you find yourself
needing to vary the :class:`SolidDefinition <dagster.SolidDefinition>` or :func:`@solid <dagster.solid>` decorator
arguments themselves, since they cannot be modified based on solid
configuration.

General solid factory pattern:

.. literalinclude:: ../../../../examples/dagster_examples/how_tos/solids.py
   :linenos:
   :lines: 80-98
   :language: python
