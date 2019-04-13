Types
=========

.. module:: dagster

Dagster type system.

Builtin Types
-------------

.. autoclass:: Any

No rules. No fear. No limits.

.. autoclass:: Bool

Validates at runtime time that ``isinstance(value, bool)``

.. autoclass:: Int

Validates at runtime time that ``isinstance(value, six.integer_types)``

.. autoclass:: Float

Validates at runtime time that ``isinstance(value, float)``

.. autoclass:: String


Validates at runtime time that ``isinstance(value, six.string_types)``

.. autoclass:: Path

Same validation as ``String``, useful for communicating that this string
represents a file path.

.. autoclass:: Nothing

A way to establish execution dependencies without communicating
values. When a solid uses :py:class:`InputDefinition` of type
``Nothing``, no parameters are passed to to the ``transform_fn``
for that input.

.. autofunction:: Nullable

.. autofunction:: List

-----

Config Types
------------

The following types are used to describe the schema of configuration
data via ``config_field``. They are used in conjunction with the
builtin types above.

.. autofunction:: Field

.. autofunction:: Dict

-----

Making New Types
----------------

.. autofunction:: as_dagster_type

.. autofunction:: dagster_type

.. autoclass:: PythonObjectType

.. autoclass:: RuntimeType

.. autoclass:: ConfigType

.. autofunction:: NamedDict


-----

Schema
------

.. autofunction:: Selector

.. autofunction:: NamedSelector

.. autofunction:: input_schema

.. autofunction:: input_selector_schema

.. autofunction:: output_schema

.. autofunction:: output_selector_schema


