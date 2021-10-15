.. currentmodule:: dagster

Execution
=========


Executing Jobs
--------------

.. autoclass:: JobDefinition
  :noindex:
  :members: execute_in_process

Executing Graphs
----------------

.. autoclass:: GraphDefinition
  :noindex:
  :members: execute_in_process

Execution results
-----------------
.. currentmodule:: dagster

.. autoclass:: InProcessExecutionResult
   :members:
   :inherited-members:

.. autoclass:: DagsterEvent
   :members:

.. autoclass:: DagsterEventType
   :members:
   :undoc-members:


Reconstructable jobs
--------------------
.. currentmodule:: dagster

.. autoclass:: reconstructable
   :members:

Executors
---------
.. autodata:: in_process_executor
  :annotation: ExecutorDefinition

.. autodata:: multiprocess_executor
  :annotation: ExecutorDefinition

.. autodata:: default_executors
  :annotation: List[ExecutorDefinition]

  The default executors available on any :py:class:`ModeDefinition` that does not provide custom
  executors. These are currently [:py:class:`in_process_executor`,
  :py:class:`multiprocess_executor`].

Contexts
--------

.. autoclass:: SystemComputeExecutionContext
  :members:
  :inherited-members:

.. autoclass:: TypeCheckContext
  :members:
  :inherited-members:

Job configuration
-----------------

.. _config_schema:

Run Config Schema
^^^^^^^^^^^^^^^^^^^^^^^
  The ``run_config`` used by :py:func:`execute_pipeline` and
  :py:func:`execute_pipeline_iterator` has the following schema:

  ::

      {
        # configuration for execution, required if executors require config
        execution: {
          # the name of one, and only one available executor, typically 'in_process' or 'multiprocess'
          __executor_name__: {
            # executor-specific config, if required or permitted
            config: {
              ...
            }
          }
        },

        # configuration for loggers, required if loggers require config
        loggers: {
          # the name of an available logger
          __logger_name__: {
            # logger-specific config, if required or permitted
            config: {
              ...
            }
          },
          ...
        },

        # configuration for resources, required if resources require config
        resources: {
          # the name of a resource
          __resource_name__: {
            # resource-specific config, if required or permitted
            config: {
              ...
            }
          },
          ...
        },

        # configuration for underlying graph, required if ops require config
        graph: {

          # these keys align with the names of the ops, or their alias in this pipeline
          __op_name__: {

            # pass any data that was defined via config_field
            config: ...,

            # configurably specify input values, keyed by input name
            inputs: {
              __input_name__: {
                # if an dagster_type_loader is specified, that schema must be satisfied here;
                # scalar, built-in types will generally allow their values to be specified directly:
                value: ...
              }
            },

          }
        },

      }
