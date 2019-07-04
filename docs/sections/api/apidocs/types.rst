Types
=========

.. module:: dagster

Dagster type system.

Builtin Types
-------------

.. attribute:: Any

    No rules. No fear. No limits.

.. attribute:: Bool

    Validates at runtime time that ``isinstance(value, bool)``

.. attribute:: Int

    Validates at runtime time that ``isinstance(value, six.integer_types)``

.. attribute:: Float

    Validates at runtime time that ``isinstance(value, float)``

.. attribute:: String

    Validates at runtime time that ``isinstance(value, six.string_types)``

.. attribute:: Path

    Same validation as ``String``, useful for communicating that this string
    represents a file path.

.. attribute:: Nothing

    A way to establish execution dependencies without communicating
    values. When a solid uses :py:class:`InputDefinition` of type
    ``Nothing``, no parameters are passed to to the ``transform_fn``
    for that input.

.. autofunction:: Optional

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

.. autofunction:: input_hydration_config

.. autofunction:: output_materialization_config
