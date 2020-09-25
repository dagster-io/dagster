dbt (dagster_dbt)
-----------------

This library provides a Dagster integration with `dbt <https://getdbt.com/>`_ (data build tool), created by `Fishtown Analytics <https://www.fishtownanalytics.com/>`_.

.. currentmodule:: dagster_dbt


CLI
~~~

.. autofunction:: dbt_cli_compile

.. autofunction:: dbt_cli_run

.. autofunction:: dbt_cli_run_operation

.. autofunction:: dbt_cli_snapshot

.. autofunction:: dbt_cli_snapshot_freshness

.. autofunction:: dbt_cli_test

.. autoclass:: DbtCliResult
    :members:

.. autoclass:: DbtCliStatsResult
    :members:


RPC
~~~

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

.. autofunction:: dbt_rpc_resource

.. autoattribute:: local_dbt_rpc_resource

.. autoclass:: DbtRpcClient
    :members:

.. autoclass:: DbtRpcPollResult
    :members:

.. autoclass:: NodeResult
    :members:

.. autoclass:: NodeTiming
    :members:


Errors
~~~~~~

.. autoexception:: DagsterDbtError

.. autoexception:: DagsterDbtCliRuntimeError

.. autoexception:: DagsterDbtFatalCliRuntimeError

.. autoexception:: DagsterDbtHandledCliRuntimeError

.. autoexception:: DagsterDbtUnexpectedCliOutputErro

.. autoexception:: DagsterDbtUnexpectedRpcPollOutput
