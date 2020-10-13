from dagster.core.utils import check_dagster_package_version

from .cli import (
    DbtCliOutput,
    dbt_cli_compile,
    dbt_cli_run,
    dbt_cli_run_operation,
    dbt_cli_snapshot,
    dbt_cli_snapshot_freshness,
    dbt_cli_test,
)
from .errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
    DagsterDbtCliRuntimeError,
    DagsterDbtCliUnexpectedOutputError,
    DagsterDbtError,
    DagsterDbtRpcUnexpectedPollOutputError,
)
from .rpc import (
    DbtRpcClient,
    DbtRpcOutput,
    create_dbt_rpc_run_sql_solid,
    dbt_rpc_compile_sql,
    dbt_rpc_resource,
    dbt_rpc_run,
    dbt_rpc_run_and_wait,
    dbt_rpc_run_operation,
    dbt_rpc_run_operation_and_wait,
    dbt_rpc_snapshot,
    dbt_rpc_snapshot_and_wait,
    dbt_rpc_snapshot_freshness,
    dbt_rpc_snapshot_freshness_and_wait,
    dbt_rpc_test,
    dbt_rpc_test_and_wait,
    local_dbt_rpc_resource,
)
from .types import DbtResult, NodeResult, StepTiming
from .version import __version__

check_dagster_package_version("dagster-dbt", __version__)

__all__ = [
    "DagsterDbtCliRuntimeError",
    "DagsterDbtCliFatalRuntimeError",
    "DagsterDbtCliHandledRuntimeError",
    "DagsterDbtCliOutputsNotFoundError",
    "DagsterDbtCliUnexpectedOutputError",
    "DagsterDbtError",
    "DagsterDbtRpcUnexpectedPollOutputError",
    "DbtCliOutput",
    "DbtResult",
    "DbtRpcClient",
    "DbtRpcOutput",
    "NodeResult",
    "StepTiming",
    "create_dbt_rpc_run_sql_solid",
    "dbt_cli_compile",
    "dbt_cli_run",
    "dbt_cli_run_operation",
    "dbt_cli_snapshot",
    "dbt_cli_snapshot_freshness",
    "dbt_cli_test",
    "dbt_rpc_compile_sql",
    "dbt_rpc_resource",
    "dbt_rpc_run",
    "dbt_rpc_run_and_wait",
    "dbt_rpc_run_operation",
    "dbt_rpc_run_operation_and_wait",
    "dbt_rpc_snapshot",
    "dbt_rpc_snapshot_and_wait",
    "dbt_rpc_snapshot_freshness",
    "dbt_rpc_snapshot_freshness_and_wait",
    "dbt_rpc_test",
    "dbt_rpc_test_and_wait",
    "local_dbt_rpc_resource",
]
