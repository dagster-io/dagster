Airlift (dagster-airlift)
=========================



Core (dagster_airlift.core)
---------------------------

.. currentmodule:: dagster_airlift.core
    
AirflowInstance
^^^^^^^^^^^^^^^^^

.. autoclass:: AirflowInstance
    :members:

.. autoclass:: AirflowAuthBackend

.. autoclass:: AirflowBasicAuthBackend 

Assets & Definitions
^^^^^^^^^^^^^^^^^^^^

.. autofunction:: build_defs_from_airflow_instance

Mapping Dagster assets to Airflow tasks/dags:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: assets_with_task_mappings

.. autofunction:: assets_with_dag_mappings

.. autofunction:: assets_with_multiple_task_mappings 

Annotations for customizable components:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: DagSelectorFn

.. autoclass:: DagsterEventTransformerFn

.. autoclass:: TaskHandleDict

Objects for retrieving information about the Airflow/Dagster mapping:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: DagInfo

.. autoclass:: AirflowDefinitionsData


MWAA (dagster_airlift.mwaa)
---------------------------
.. currentmodule:: dagster_airlift.mwaa

.. autoclass:: MwaaSessionAuthBackend

In Airflow (dagster_airlift.in_airflow)
---------------------------------------

.. currentmodule:: dagster_airlift.in_airflow

Proxying
^^^^^^^^^

.. autofunction:: proxying_to_dagster 

.. autoclass:: BaseDagsterAssetsOperator
    
.. autofunction:: load_proxied_state_from_yaml

Proxying State
~~~~~~~~~~~~~~

.. autoclass:: AirflowProxiedState

.. autoclass:: DagProxiedState

.. autoclass:: TaskProxiedState

Task-level Proxying
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: BaseProxyTaskToDagsterOperator

.. autoclass:: DefaultProxyTaskToDagsterOperator
  
Dag-level Proxying
~~~~~~~~~~~~~~~~~~~

.. autoclass:: BaseProxyDAGToDagsterOperator

.. autoclass:: DefaultProxyDAGToDagsterOperator


