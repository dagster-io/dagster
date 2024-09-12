Config
======

.. currentmodule:: dagster

Pythonic config system
----------------------

The following classes are used as part of the new `Pythonic config system <https://docs.dagster.io/concepts/configuration/config-schema>`_. They are used in conjunction with builtin types.

.. autoclass:: Config

.. autoclass:: PermissiveConfig

.. autoclass:: RunConfig

Legacy Dagster config types
---------------------------

The following types are used as part of the legacy `Dagster config system <https://docs.dagster.io/concepts/configuration/config-schema-legacy>`_. They are used in conjunction with builtin types.

.. autoclass:: ConfigSchema

.. autoclass:: Field

.. autoclass:: Selector

.. autoclass:: Permissive

.. autoclass:: Shape

.. autoclass:: Map

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

        from dagster import job, op, StringSource

        @op(config_schema=StringSource)
        def secret_op(context) -> str:
            return context.op_config

        @job
        def secret_job():
            secret_op()

        secret_job.execute_in_process(
            run_config={
                'ops': {'secret_op': {'config': 'test_value'}}
            }
        )

        secret_job.execute_in_process(
            run_config={
                'ops': {'secret_op': {'config': {'env': 'VERY_SECRET_ENV_VARIABLE'}}}
            }
        )

.. attribute:: IntSource

   Use this type when you want to read an integer config value from an environment variable. The
   value passed to a config field of this type may either be a integer literal, or a selector
   describing how to look up the value from the executing process's environment variables.

   **Examples:**

   .. code-block:: python

        from dagster import job, op, IntSource

        @op(config_schema=IntSource)
        def secret_int_op(context) -> int:
            return context.op_config

        @job
        def secret_job():
            secret_int_op()

        secret_job.execute_in_process(
            run_config={
                'ops': {'secret_int_op': {'config': 1234}}
            }
        )

        secret_job.execute_in_process(
            run_config={
                'ops': {'secret_int_op': {'config': {'env': 'VERY_SECRET_ENV_VARIABLE_INT'}}}
            }
        )

.. attribute:: BoolSource

   Use this type when you want to read an boolean config value from an environment variable. The
   value passed to a config field of this type may either be a boolean literal, or a selector
   describing how to look up the value from the executing process's environment variables. Set the
   value of the corresponding environment variable to ``""`` to indicate ``False``.

   **Examples:**

   .. code-block:: python

        from dagster import job, op, BoolSource

        @op(config_schema=BoolSource)
        def secret_bool_op(context) -> bool:
            return context.op_config

        @job
        def secret_job():
            secret_bool_op()

        secret_job.execute_in_process(
            run_config={
                'ops': {'secret_bool_op': {'config': False}}
            }
        )

        secret_job.execute_in_process(
            run_config={
                'ops': {'secret_bool_op': {'config': {'env': 'VERY_SECRET_ENV_VARIABLE_BOOL'}}}
            }
        )


Config Utilities
----------------

.. autoclass:: ConfigMapping

.. autodecorator:: configured
