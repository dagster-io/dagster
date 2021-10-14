Execution
=========

.. currentmodule:: dagster

Executing pipelines
-------------------

.. autofunction:: execute_pipeline

.. autofunction:: execute_pipeline_iterator

Re-executing pipelines
-------------------

.. autofunction:: reexecute_pipeline

.. autofunction:: reexecute_pipeline_iterator

Executing solids
----------------
.. currentmodule:: dagster

.. autofunction:: execute_solid

.. autofunction:: execute_solid_within_pipeline

.. autofunction:: execute_solids_within_pipeline

Execution context
-----------------
.. currentmodule:: dagster

.. autoclass:: SolidExecutionContext
   :members:
   :inherited-members:

.. autofunction:: build_solid_context

Validating Execution
--------------------
.. currentmodule:: dagster

.. autofunction:: validate_run_config


Reconstructable pipelines
-------------------------
.. currentmodule:: dagster

.. autoclass:: reconstructable
   :members:

.. currentmodule:: dagster.core.definitions.reconstructable

.. autoclass:: ReeconstructablePipeline
   :members:

.. autofunction:: build_reconstructable_pipeline

Pipeline and solid results
--------------------------
.. currentmodule:: dagster

.. autoclass:: PipelineExecutionResult
   :members:
   :inherited-members:

.. autoclass:: SolidExecutionResult
   :members:
   :inherited-members:

.. autoclass:: CompositeSolidExecutionResult
   :members:
   :inherited-members:

.. autoclass:: DagsterEvent
   :members:

.. autoclass:: DagsterEventType
   :members:
   :undoc-members:

Pipeline configuration
----------------------

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

        # configuration for solids, required if solids require config
        solids: {

          # these keys align with the names of the solids, or their alias in this pipeline
          __solid_name__: {

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

            # configurably materialize output values
            outputs: {
              __output_name__: {
                # if an dagster_type_materializer is specified, that schema must be satisfied
                # here; pickleable types will generally allow output as follows:
                pickle: {
                  path: String
                }
              }
            }
          }
        },

        # optionally use an available system storage for intermediates etc.
        intermediate_storage: {
          # the name of one, and only one available system storage, typically 'filesystem' or
          # 'in_memory'
          __storage_name__: {
            config: {
              ...
            }
          }
        }
      }


Intermediate Storage
--------------------
.. autofunction:: io_manager_from_intermediate_storage

.. autodata:: mem_intermediate_storage
  :annotation: IntermediateStorageDefinition

.. autodata:: fs_intermediate_storage
  :annotation: IntermediateStorageDefinition

.. autodata:: default_intermediate_storage_defs
  :annotation: List[IntermediateStorageDefinition]

  The default intermediate storages available on any :py:class:`ModeDefinition` that does not provide
  custom intermediate storages. These are currently [:py:class:`mem_intermediate_storage`,
  :py:class:`fs_intermediate_storage`].

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
