Metadata and custom type checks
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

Custom type checks and metadata are appropriate for checking that a value will behave as we expect,
and for collecting summary information about values.
