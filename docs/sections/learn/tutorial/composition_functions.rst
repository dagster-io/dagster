Composition Functions
---------------------

To ease the process of building up graphs of computations, we provide an API of simply
executing code to produce the dependencies between solids. We call these “composition functions”
and are used with the :py:func:`@pipeline <dagster.pipeline>` and
:py:func:`@composite_solid <dagster.composite_solid>` decorators.

While in a composition function, every time a solid is invoked it is recorded and added
to the current computation graph. The outputs from one solid invocation are passed to the next to establish
a dependency.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 21-24
   :caption: composition.py

Solids that have multiple outputs return a named tuple representing the outputs.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 123-132
   :caption: composition.py


Aliases
^^^^^^^

If the same solid is invoked multiple times, we need to give each invocation a unique name. This is done
automatically using a simple integer suffix.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 27-32
   :emphasize-lines: 5
   :caption: composition.py


While the automatic aliasing is useful for getting started, it is often preferable to give the invocations
more useful names. The ``alias`` function returns an instance of the solid with the provided name which
can then be invoked.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 135-140
   :emphasize-lines: 4-5
   :caption: composition.py


Composite Solids
^^^^^^^^^^^^^^^^

Composition functions for composite solids are slightly more complicated since they allow you express
input and output mappings.

Input Mapping
*************

You can declare inputs for your composite solid explicitly by passing InputDefinitions to the
decorator or have them inferred from your type signature. When we invoke the function we will
pass InputMappingNodes for each input which can then be captured as mappings when used as an
argument when invoking a solid.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 35-37
   :caption: composition.py


Output Mapping
**************

You can declare outputs for your composite by explicitly passing OutputDefinitions
to the decorator or have them inferred from the type signature.

The value returned from the composition function will determine the output mapping.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 40-43
   :caption: composition.py

Note you can not communicate multiple outputs via type signature at this time (https://github.com/dagster-io/dagster/issues/1529),
so if you have multiple outputs you’ll have to declare them explicitly.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/composition.py
   :linenos:
   :lines: 45-50
   :caption: composition.py
