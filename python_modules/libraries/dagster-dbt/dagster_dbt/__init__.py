from dagster._core.utils import check_dagster_package_version

from .asset_defs import load_assets_from_dbt_manifest, load_assets_from_dbt_project
from .cli import DbtCliOutput, DbtCliResource, dbt_cli_resource
from .cloud import (
    DbtCloudOutput,
    DbtCloudResourceV2,
    dbt_cloud_resource,
    dbt_cloud_run_op,
    load_assets_from_dbt_cloud_job,
)
from .dbt_resource import DbtResource
from .errors import (
    DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError,
    DagsterDbtCliRuntimeError,
    DagsterDbtCliUnexpectedOutputError,
    DagsterDbtCloudJobInvariantViolationError,
    DagsterDbtError,
    DagsterDbtRpcUnexpectedPollOutputError,
)
from .ops import (
    dbt_build_op,
    dbt_compile_op,
    dbt_docs_generate_op,
    dbt_ls_op,
    dbt_run_op,
    dbt_seed_op,
    dbt_snapshot_op,
    dbt_test_op,
)
from .rpc import (
    DbtRpcOutput,
    DbtRpcResource,
    DbtRpcSyncResource,
    dbt_rpc_resource,
    dbt_rpc_sync_resource,
    local_dbt_rpc_resource,
)
from .types import DbtOutput
from .version import __version__

check_dagster_package_version("dagster-dbt", __version__)

__all__ = [
    "DagsterDbtCliRuntimeError",
    "DagsterDbtCliFatalRuntimeError",
    "DagsterDbtCliHandledRuntimeError",
    "DagsterDbtCliOutputsNotFoundError",
    "dbt_cli_resource",
    "dbt_rpc_resource",
    "dbt_rpc_sync_resource",
    "DagsterDbtCliUnexpectedOutputError",
    "DagsterDbtError",
    "DagsterDbtRpcUnexpectedPollOutputError",
    "DbtResource",
    "DbtOutput",
    "DbtCliOutput",
    "DbtCliResource",
    "DbtCloudOutput",
    "DbtCloudResourceV2",
    "DbtRpcResource",
    "DbtRpcSyncResource",
    "DbtRpcOutput",
    "dbt_cloud_resource",
    "dbt_cloud_run_op",
    "local_dbt_rpc_resource",
]
