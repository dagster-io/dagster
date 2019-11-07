Execution
=========

.. currentmodule:: dagster

Executing pipelines
-------------------

.. autofunction:: execute_pipeline

.. autofunction:: execute_pipeline_iterator

.. autofunction:: execute_pipeline_with_preset

Executing solids
----------------

.. autofunction:: execute_solid

.. autofunction:: execute_solid_within_pipeline

.. autofunction:: execute_solids_within_pipeline

Execution context
-----------------

.. autoclass:: SystemComputeExecutionContext
   :members:

Pipeline and solid results
--------------------------

.. autoclass:: PipelineExecutionResult
   :members:

.. autoclass:: SolidExecutionResult
   :members:

.. autoclass:: DagsterEvent
   :members:

.. autoclass:: DagsterEventType
   :members:
   :undoc-members:

Pipeline configuration
----------------------

.. _config_schema:

Environment Dict Schema
^^^^^^^^^^^^^^^^^^^^^^^
  The ``environment_dict`` used by :py:func:`execute_pipeline` and
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

        # configuration for solids, required if solids require config
        solids: {

          # these keys align with the names of the solids, or their alias in this pipeline
          __solid_name__: {

            # pass any data that was defined via config_field
            config: ...,

            # configurably specify input values, keyed by input name
            inputs: {
              __input_name__: {
                # if an input_hydration_config is specified, that schema must be satisfied here;
                # scalar, built-in types will generally allow their values to be specified directly:
                value: ...
              }
            },

            # configurably materialize output values
            outputs: {
              __output_name__: {
                # if an output_materialization_config is specified, that schema must be satisfied
                # here; pickleable types will generally allow output as follows:
                pickle: {
                  path: Path
                }
              }
            }
          }
        },

        # optionally use an available system storage for intermediates etc.
        storage: {
          # the name of one, and only one available system storage, typically 'filesystem' or
          # 'in_memory'
          __storage_name__: {
            config: {
              ...
            }
          }
        }
      }

.. autoclass:: RunConfig
   :members:
