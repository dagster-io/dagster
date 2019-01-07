Types
=========

.. module:: dagster.core.types

Dagster type system.

Type definitions
-----------------

.. autoclass:: DagsterBuiltinScalarType
    :members: is_python_valid_value

.. autoclass:: DagsterScalarType
    :members: is_python_valid_value

.. autoclass:: DagsterStringType
    :members: is_python_valid_value

.. autoclass:: DagsterType
    :members:

.. autofunction:: Dict

.. autoclass:: PythonObjectType

.. autodata:: Any

.. autofunction:: Nullable

.. autofunction:: List

.. autodata:: String

.. autodata:: Path

.. autodata:: Int

.. autodata:: Bool

.. autoclass:: UncoercedTypeMixin

Utilities
------------

.. autoclass:: Configurable
   :members:

.. autoclass:: ConfigurableFromAny
   :members:

.. autoclass:: ConfigurableFromList
   :members:

.. autoclass:: ConfigurableFromNullable
   :members:

.. autoclass:: ConfigurableFromScalar
   :members:

.. autoclass:: ConfigurableObjectFromDict
   :members:

.. autoclass:: ConfigurableSelectorFromDict
   :members:

.. autoclass:: Field
   :members: