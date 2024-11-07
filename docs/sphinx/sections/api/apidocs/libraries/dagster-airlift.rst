Airlift (dagster-airlift)
=========================



Core (dagster_airlift.core)
---------------------------

.. currentmodule:: dagster_airlift.core
    
AirflowInstance
^^^^^^^^^^^^^^^^^

.. autoclass:: AirflowInstance

.. autoclass:: AirflowAuthBackend

.. autoclass:: AirflowBasicAuthBackend 


Assets & Definitions
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: build_defs_from_airflow_instance

Annotations for customizable components:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: DagSelectorFn

.. autoclass:: DagsterEventTransformerFn

Objects for retrieving information about the Airflow/Dagster mapping:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: DagInfo

.. autoclass:: AirflowDefinitionsData




MWAA (dagster_airlift.mwaa)
---------------------------
.. currentmodule:: dagster_airlift.mwaa

.. autoclass:: MwaaSessionAuthBackend


