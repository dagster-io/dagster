Types
=========

.. module:: dagster.core.types

Dagster type system.

Type definitions
-----------------

.. autoclass:: DagsterType
    :members:

.. autoclass:: DagsterScalarType
    :members: process_value, is_python_valid_value

.. autoclass:: DagsterCompositeType

.. autoclass:: ConfigDictionary

.. autoclass:: PythonObjectType

.. autodata:: Any

.. autodata:: String

.. autodata:: Path

.. autodata:: Int

.. autodata:: Bool

Utilities
------------

.. autoclass:: Field
   :members:

.. autoclass:: IncomingValueResult
   :members:
