Types
=========

.. module:: dagster

Dagster type system.

Scalar Types
------------
.. autoclass:: Any

.. autoclass:: Bool

.. autoclass:: Int

.. autoclass:: String

.. autoclass:: Path

Wrapper Types
-------------

.. autofunction:: Nullable

.. autofunction:: List

.. autofunction:: Field

.. autofunction:: Dict

.. autofunction:: NamedDict

.. autoclass:: ConfigType

Schema
------

.. autofunction:: input_schema

.. autofunction:: input_selector_schema

.. autofunction:: output_schema

.. autofunction:: output_selector_schema


Making New Types
----------------
.. autoclass:: PythonObjectType

.. autofunction:: as_dagster_type

.. autofunction:: dagster_type
