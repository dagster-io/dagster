Validating Pandas DataFrames with Dagster Types
------------------------------------------------
   * :ref:`Creating Dagster DataFrame Types <creating_dagster_dataframes>`
   * :ref:`Dagster DataFrame Level Validation <dataframe_level_validation>`
   * :ref:`Dagster DataFrame Custom Validation <custom_validation>`

Pandas is a broadly adopted library for data transformations. Dagster pandas is a library that provides the ability to
easily express custom dataframe types that perform data validation, emit summary statistics,
and enable reliable dataframe serialization/deserialization. On top of this, the dagster type system generates
documentation of your dataframe constraints and makes it accessible via Dagit.

.. _creating_dagster_dataframes:

Creating Dagster DataFrame Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a custom dagster pandas type, use ``create_dagster_pandas_dataframe_type`` and provide a list of
``PandasColumn`` objects which specify column-level schema and constraints. For example, we can construct
a custom dataframe type to represent a set of e-bike trips in the following way:

.. literalinclude:: ../../../../../examples/dagster_examples/dagster_pandas_guide/core_trip_pipeline.py
   :caption: core_trip_pipeline.py
   :lines: 9-22
   :language: python

Once our custom data type is defined, we can use it as the type declaration for the inputs / outputs of our solid:

.. literalinclude:: ../../../../../examples/dagster_examples/dagster_pandas_guide/core_trip_pipeline.py
   :caption: core_trip_pipeline.py
   :lines: 25-31
   :language: python

By passing in these ``PandasColumn`` objects, we are expressing the schema and constraints we expect our dataframes
to follow when dagster performs type checks for our solids. Moreover, if we go to the solid viewer, we can
follow our schema documented in dagit:

.. thumbnail:: tutorial2.png

.. _dataframe_level_validation:

Dagster DataFrame Level Validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that we have a custom dataframe type that performs schema validation during a pipeline run, we can start to
express dataframe level constraints (e.g number of rows, or columns).

We can do this by providing a list of dataframe constraints to ``create_dagster_pandas_dataframe_type``. These
constraint objects live in ``dagster_pandas/constraints.py``. Two such constraints are
the ``RowCountConstraint`` and ``StrictColumnsConstraint``.

This looks like:

.. literalinclude:: ../../../../../examples/dagster_examples/dagster_pandas_guide/shape_constrained_pipeline.py
   :lines: 9-11
   :caption: shape_constrained_pipeline.py
   :language: python

If we rerun the above example with this dataframe, nothing should change. However, if we pass in 100 to the row
count constraint, we can watch our pipeline fail that type check.

.. _dataframe_summary_statistics:

Dagster DataFrame Summary Statistics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Aside from constraint validation, ``create_dagster_pandas_dataframe_type`` also takes in a summary statistics function
that emits ``EventMetadataEntry`` objects which are surfaced during pipeline runs. Since data systems seldom control
the quality of the data they receive, it becomes important to monitor data as it flows through your systems. In complex
pipelines, this can help debug and monitor data drift over time. Let's illustrate how this works in our example:

.. literalinclude:: ../../../../../examples/dagster_examples/dagster_pandas_guide/summary_stats_pipeline.py
   :lines: 10-39
   :caption: summary_stats_pipeline.py
   :language: python

Now if we run this pipeline in the dagit playground:

.. thumbnail:: tutorial1.png

.. _custom_validation:

Dagster DataFrame Custom Validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``PandasColumn`` is user-pluggable with custom constraints. They can be constructed directly and passed a list of
``ColumnConstraint`` objects.

To tie this back to our example, let's say that we want to validate that the amount paid for a e-bike must be in
5 dollar increments because that is the price per mile rounded up. As a result, let's implement
a ``DivisibleByFiveConstraint``. To do this, all it needs is a ``markdown_description`` for dagit which accepts and
renders markdown syntax, an ``error_description`` for error logs, and a validation method which throws a
``ColumnConstraintViolationException`` if a row fails validation. This would look like the following:

.. literalinclude:: ../../../../../examples/dagster_examples/dagster_pandas_guide/custom_column_constraint_pipeline.py
   :lines: 15-40
   :caption: custom_column_constraint_pipeline.py
   :emphasize-lines: 22-24
   :language: python
