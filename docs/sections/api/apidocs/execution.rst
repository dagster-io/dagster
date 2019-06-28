Execution
=========

.. currentmodule:: dagster

Execution Functions
-------------------

.. autofunction:: execute_pipeline

.. autofunction:: execute_pipeline_iterator

Results
-------

.. autoclass:: PipelineExecutionResult
   :members:

.. autoclass:: SolidExecutionResult
   :members:

Configuration
-------------
**Environment Dict Schema**
  The ``environment_dict`` used by ``execute_pipeline`` and
  ``execute_pipeline_iterator`` has the following schema:
  ::

    {
      # configuration for Solids
      'solids': {

        # these keys align with the names of the solids, or their alias in this pipeline
        '_solid_name_': {

          # pass any data that was defined via config_field
          'config': _,

           # materialize input values, keyed by input name
          'inputs': {
            '_input_name_': {'value': _value_}
          }
        }
      }
    }

.. autoclass:: RunConfig
   :members:

.. autoclass:: InProcessExecutorConfig
   :members:

.. autoclass:: MultiprocessExecutorConfig
   :members:
