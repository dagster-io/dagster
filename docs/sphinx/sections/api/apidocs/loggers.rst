Loggers
=======

Built-in loggers
----------------
.. currentmodule:: dagster.loggers

.. autoclass colored_console_logger

.. autoclass json_console_logger

Logging from a solid
--------------------
.. currentmodule:: dagster

.. autoclass DagsterLogManager

Defining custom loggers
-----------------------
.. currentmodule:: dagster

.. autodecorator:: logger

.. autoclass:: LoggerDefinition
    :members: configured

.. autoclass:: InitLoggerContext

.. autofunction:: build_init_logger_context

Monitoring stdout and stderr
----------------------------
.. currentmodule:: dagster
