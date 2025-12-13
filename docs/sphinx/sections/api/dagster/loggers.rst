Loggers
=======

Built-in loggers
----------------
.. currentmodule:: dagster._loggers

.. autofunction:: colored_console_logger

.. autofunction:: json_console_logger

Logging from an @op
--------------------
.. currentmodule:: dagster

.. autoclass:: DagsterLogManager

Defining custom loggers
-----------------------
.. currentmodule:: dagster

.. autodecorator:: logger

.. autoclass:: LoggerDefinition
    :members: configured

.. autoclass:: InitLoggerContext

.. autofunction:: build_init_logger_context
