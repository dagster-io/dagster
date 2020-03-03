.. _expectations:

Expectations
------------

But sometimes we want to make more specific, data- and business logic-dependent assertions about
the semantics of values. It typically isn't appropriate to embed assertions like these into data
types directly.

For one, they will usually vary substantially between instantiations -- for example, we don't
expect all data frames to have the same number of columns, and over-specifying data types (e.g.,
``SixColumnedDataFrame``) makes it difficult for generic logic to work generically (e.g., over all
data frames).

What's more, these additional, deeper semantic assertions are often non-stationary. Typically,
you'll start running a pipeline with certain expectations about the data that you'll see; but
over time, you'll learn more about your data (making your expectations more precise), and the
process in the world that generates your data will shift (making some of your expectations invalid.)

We've already encountered the :py:class:`TypeCheck <dagster.TypeCheck>` event, which
is typically yielded by the type machinery (but can also be yielded manually from the body of a
solid's compute function); :py:class:`ExpectationResult <dagster.ExpectationResult>` is another
kind of structured side-channel result that a solid can yield. These extra events don't get passed
to downstream solids and they aren't used to define the data dependencies of a pipeline DAG.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_bad_5.py
   :lines: 91-133
   :linenos:
   :lineno-start: 91
   :emphasize-lines: 1-3, 31
   :caption: custom_types_bad_5.py
   :language: python


Until now, every solid we've encountered has returned its result value, or ``None``. But solids can
also yield events of various types for side-channel communication about the results of their
computations.

Running this pipeline yields an :py:class:`ExpectationResult <dagster.ExpectationResult>` with
``success`` set to ``False`` since we expect entries in the ``calories`` column to be of type
``int`` but they are of type ``string``. We note that this precedes our incorrect result that the
least caloric cereal is Corn Flakes (100 calories per serving) and the most caloric cereal
Strawberry Fruit Wheats (90 calories per serving).

.. thumbnail:: custom_types_bad_data.png


To fix this, we can cast ``calories`` to ``int`` during the hydration process:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_5.py
   :lines: 74-83
   :linenos:
   :lineno-start: 74
   :emphasize-lines: 6
   :caption: custom_types_5.py
   :language: python

Running this pipeline yields an :py:class:`ExpectationResult <dagster.ExpectationResult>` with
``success`` set to ``True`` and the correct result that the least caloric cereal is All-Bran with
Extra Fiber (50 calories per serving) and the most caloric cereal is Mueslix Crispy Blend (160
calories per serving).

If you're already using the `Great Expectations <https://greatexpectations.io/>`_ library
to express expectations about your data, you may be interested in the ``dagster_ge`` wrapper
library.

This part of this system remains relatively immature, but yielding structured expectation results
from your solid logic means that in future, tools like Dagit will be able to aggregate and track
expectation results, as well as implement sophisticated policy engines to drive alerting and
exception handling on a deep semantic basis.
