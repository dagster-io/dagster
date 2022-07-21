.. currentmodule:: dagster

[Legacy] Pipelines
==================

As of Dagster 0.13.0, we recommend using `Jobs` as an alternative to `Pipelines`.

Pipeline definitions
--------------------
.. autodecorator:: pipeline

.. autoclass:: PipelineDefinition

Executing pipelines
-------------------

.. autofunction:: execute_pipeline

.. autofunction:: execute_pipeline_iterator

.. autoclass:: PipelineExecutionResult
   :members:
   :inherited-members:

.. autodata:: default_executors
  :annotation: List[ExecutorDefinition]

  The default executors available on any :py:class:`ModeDefinition` that does not provide custom
  executors. These are currently [:py:class:`in_process_executor`,
  :py:class:`multiprocess_executor`].


Re-executing pipelines
----------------------

.. autofunction:: reexecute_pipeline

.. autofunction:: reexecute_pipeline_iterator

Reconstructable pipelines
-------------------------
.. currentmodule:: dagster

.. autoclass:: reconstructable
   :noindex:

.. currentmodule:: dagster._core.definitions.reconstruct

.. autoclass:: ReconstructablePipeline
   :members:


Pipeline configuration
----------------------

.. _pipeline_config_schema:

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

          }
        },

      }

Aliases
-------

.. currentmodule:: dagster

.. autoclass:: SolidInvocation
