Config
======

.. currentmodule:: dagster

Config Types
------------

The following types are used to describe the schema of configuration
data via ``config``. They are used in conjunction with the
builtin types above.

.. autoclass:: ConfigSchema

.. autoclass:: Field

.. autoclass:: Selector

.. autoclass:: Permissive

.. autoclass:: Shape

.. autoclass:: Array

.. autoclass:: Noneable

.. autoclass:: Enum
    :members: from_python_enum

.. autoclass:: EnumValue

.. autoclass:: ScalarUnion

.. attribute:: StringSource

   Use this type when you want to read a string config value from an environment variable. The value
   passed to a config field of this type may either be a string literal, or a selector describing
   how to look up the value from the executing process's environment variables.

   **Examples:**

   .. code-block:: python

        @solid(config_schema=StringSource)
        def secret_solid(context) -> str:
            return context.solid_config

        execute_solid(
            secret_solid,
            run_config={
                'solids': {'secret_solid': {'config': 'test_value'}}
            }
        )

        execute_solid(
            secret_solid,
            run_config={
                'solids': {'secret_solid': {'config': {'env': 'VERY_SECRET_ENV_VARIABLE'}}}
            }
        )

.. attribute:: IntSource

   Use this type when you want to read an integer config value from an environment variable. The
   value passed to a config field of this type may either be a integer literal, or a selector
   describing how to look up the value from the executing process's environment variables.

   **Examples:**

   .. code-block:: python

        @solid(config_schema=IntSource)
        def secret_int_solid(context) -> str:
            return context.solid_config

        execute_solid(
            secret_int_solid,
            run_config={
                'solids': {'secret_int_solid': {'config': 3}}
            }
        )

        execute_solid(
            secret_int_solid,
            run_config={
                'solids': {'secret_int_solid': {'config': {'env': 'VERY_SECRET_ENV_VARIABLE_INT'}}}
            }
        )

Config Utilities
----------------

.. autodecorator:: configured
