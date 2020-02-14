Metadata and data quality checks
--------------------------------

.. toctree::
  :maxdepth: 1
  :hidden:

Custom types can also yield metadata about the type check. For example, in the case of our data
frame, we might want to record the number of rows and columns in the dataset when our type checks
succeed, and provide more information about why type checks failed when they fail.

User-defined type check functions can optionally return a :py:class:`TypeCheck <dagster.TypeCheck>`
object that contains metadata about the success or failure of the type check.

Let's see how to use this to emit some summary statistics about our DataFrame type:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_4.py
   :lines: 17-69
   :linenos:
   :lineno-start: 17
   :emphasize-lines: 3-9, 33-53
   :caption: custom_types_4.py
   :language: python

A :py:class:`TypeCheck <dagster.TypeCheck>` must include a ``success`` argument describing whether
the check passed or failed, and may include a description and/or a list of
:py:class:`EventMetadataEntry <dagster.EventMetadataEntry>` objects. You should use the
static constructors on :py:class:`EventMetadataEntry <dagster.EventMetadataEntry>` to construct
these objects, which are flexible enough to support arbitrary metadata in JSON or Markdown format.

Dagit knows how to display and archive structured metadata of this kind for future review:

.. thumbnail:: custom_types_figure_two.png


Expectations
^^^^^^^^^^^^

Custom type checks and metadata are appropriate for checking that a value will behave as we expect,
and for collecting summary information about values.

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

To support this kind of assertion, Dagster includes support for expressing your expectations about
data in solid logic.

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/custom_types_5.py
   :lines: 91-133
   :linenos:
   :lineno-start: 91
   :emphasize-lines: 1-3, 31
   :caption: custom_types_5.py
   :language: python

Until now, every solid we've encountered has returned its result value, or ``None``. But solids can
also yield events of various types for side-channel communication about the results of their
computations. We've already encountered the :py:class:`TypeCheck <dagster.TypeCheck>` event, which
is typically yielded by the type machinery (but can also be yielded manually from the body of a
solid's compute function); :py:class:`ExpectationResult <dagster.ExpectationResult>` is another
kind of structured side-channel result that a solid can yield. These extra events don't get passed
to downstream solids and they aren't used to define the data dependencies of a pipeline DAG.

If you're already using the `Great Expectations <https://greatexpectations.io/>`_ library
to express expectations about your data, you may be interested in the ``dagster_ge`` wrapper
library.

This part of this system remains relatively immature, but yielding structured expectation results
from your solid logic means that in future, tools like Dagit will be able to aggregate and track
expectation results, as well as implement sophisticated policy engines to drive alerting and
exception handling on a deep semantic basis.
