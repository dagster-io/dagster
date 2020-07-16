Pandas (dagster_pandas)
------------------------

The `dagster_pandas` library provides utilities for using pandas with Dagster and for implementing
validation on pandas `DataFrames`. A good place to start with `dagster_pandas` is the `validation
guide </overview/packages/dagster_pandas>`_.


.. currentmodule:: dagster_pandas

.. autofunction:: create_dagster_pandas_dataframe_type

.. autoclass:: RowCountConstraint

.. autoclass:: StrictColumnsConstraint

.. autoclass:: PandasColumn
   :members:

.. autodata:: DataFrame
