Config 
======

.. currentmodule:: dagster

The following types are used to describe the schema of configuration
data via ``config``. They are used in conjunction with the
builtin types above.

.. autoclass:: Field

.. autoclass:: Selector

.. autoclass:: Permissive

.. autoclass:: Shape 

.. autoclass:: Array 

.. autoclass:: Noneable 

.. autoclass:: Enum

.. autoclass:: EnumValue

.. attribute:: StringSource

   Use this type only for config fields. The value passed to a config field of this type may either
   be a string, or a selector describing where to look up the value in the environment.

   **Examples:**

   .. code-block:: python

        @solid(config=StringSource)
        def secret_solid(context) -> str:
            return context.solid_config

        execute_solid(
            secret_solid,
            environment_dict={
                'solids': {'secret_solid': {'config': 'test_value'}}
            }
        )

        execute_solid(
            secret_solid,
            environment_dict={
                'solids': {'secret_solid': {'config': {'env': 'VERY_SECRET_ENV_VARIABLE'}}}
            }
        )
