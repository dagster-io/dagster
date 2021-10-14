dbt (dagster-dbt)
-----------------

This library provides a Dagster integration with `dbt <https://getdbt.com/>`_ (data build tool), created by `Fishtown Analytics <https://www.fishtownanalytics.com/>`_.

.. currentmodule:: dagster_dbt


CLI
~~~

.. autodata:: dbt_cli_resource
    :annotation: ResourceDefinition

.. autoclass:: DbtCliResource
    :members:

.. autoclass:: DbtCliOutput
    :members:

.. autofunction:: dbt_cli_compile

.. autofunction:: dbt_cli_run

.. autofunction:: dbt_cli_run_operation

.. autofunction:: dbt_cli_snapshot

.. autofunction:: dbt_cli_snapshot_freshness

.. autofunction:: dbt_cli_test



RPC
~~~

.. autodata:: dbt_rpc_resource
    :annotation: ResourceDefinition

.. autodata:: local_dbt_rpc_resource
    :annotation: ResourceDefinition

.. autoclass:: DbtRpcClient
    :members:

.. autoclass:: DbtRpcOutput
    :members:

.. autofunction:: create_dbt_rpc_run_sql_solid

.. autofunction:: dbt_rpc_compile_sql

.. autofunction:: dbt_rpc_run

.. autofunction:: dbt_rpc_run_and_wait

.. autofunction:: dbt_rpc_run_operation

.. autofunction:: dbt_rpc_run_operation_and_wait

.. autofunction:: dbt_rpc_snapshot

.. autofunction:: dbt_rpc_snapshot_and_wait

.. autofunction:: dbt_rpc_snapshot_freshness

.. autofunction:: dbt_rpc_snapshot_freshness_and_wait

.. autofunction:: dbt_rpc_test

.. autofunction:: dbt_rpc_test_and_wait

Types
~~~~~

.. autoclass:: DbtOutput
    :members:

.. autoclass:: DbtResource
    :members:

Errors
~~~~~~

.. autoexception:: DagsterDbtError

.. autoexception:: DagsterDbtCliRuntimeError

.. autoexception:: DagsterDbtCliFatalRuntimeError

.. autoexception:: DagsterDbtCliHandledRuntimeError

.. autoexception:: DagsterDbtCliOutputsNotFoundError

.. autoexception:: DagsterDbtCliUnexpectedOutputError

.. autoexception:: DagsterDbtRpcUnexpectedPollOutputError
